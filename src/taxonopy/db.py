# -*- coding: utf-8 -*-

import os
import abc
from collections import OrderedDict
from collections.abc import ByteString, Iterable, Mapping, Sequence

from anytree.resolver import ChildResolverError
from natsort import natsorted
from tinydb import table, TinyDB, Query
from tinydb.middlewares import CachingMiddleware, Middleware
from tinydb.storages import JSONStorage, MemoryStorage

from .schema import SCHTree, get_node_attr


class WriteSortMiddleware(Middleware):
    
    def __init__(self, storage_cls):
        super(WriteSortMiddleware, self).__init__(storage_cls)
    
    def read(self):
        data = self.storage.read()
        return data
    
    def write(self, data):
        data = _order_data(data)
        self.storage.write(data)
    
    def close(self):
        self.storage.close()


class DataBase(metaclass=abc.ABCMeta):
    
    def __init__(self, *args, **kwargs):
        self._db = self._get_db(*args, **kwargs)
    
    def __enter__(self):
        self._db.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._db.__exit__(exc_type, exc_val, exc_tb)
    
    @abc.abstractmethod
    def _get_db(self, *args, **kwargs):
        pass
    
    @abc.abstractmethod
    def _get_repr(self):
        pass
    
    def close(self):
        self._db.close()
    
    def insert(self, record):
        self._db.insert(record.to_dict())
    
    def remove(self, doc_ids):
        self._db.remove(doc_ids=doc_ids)
    
    def replace(self, doc_id, record):
        self.remove([doc_id])
        self._db.insert(table.Document(record.to_dict(), doc_id=doc_id))
    
    def flush(self):
        null = lambda x: x
        self._db._update_table(null)
    
    def count(self, query):
        return self._db.count(query)
    
    def search(self, query):
        documents = self._db.search(query)
        if not documents: documents = None
        return MemoryDataBase(documents)
    
    def to_records(self):
        sorter = _get_doc_sorter()
        return OrderedDict((doc.doc_id, SCHTree.from_dict(dict(doc)))
                                   for doc in sorted(self._db, key=sorter))
    
    def projection(self, paths=None):
        
        def _get_node_props(node):
            
            result = get_node_attr(node)
            
            if not node.children: return result
            
            sorter = _get_node_sorter()
            child_names = [child.name for child in sorted(node.children,
                                                          key=sorter)]
            result["children"] = child_names
            
            return result
        
        if not _is_iterable(paths):
            paths = (paths,)
        
        records = self.to_records()
        result = {"id": [rid for rid in records.keys()]}
        
        for path in paths:
            
            values = []
            
            for record in records.values():
                
                node = None
                
                if path is None:
                    node = record.root_node
                    path = node.name
                else:
                    try:
                        node = record.find_by_path(path)
                    except ChildResolverError:
                        pass
                
                if node is None:
                    value = {}
                else:
                    value = _get_node_props(node)
                
                values.append(value)
            
            result[path] = values
        
        return result
    
    def __len__(self):
        return len(self._db)
    
    def __repr__(self):
        return f"<{self._get_repr()}>"


class JSONDataBase(DataBase):
    
    def _get_db(self, db_path="db.json",
                      check_existing=False,
                      access_mode='r+'):
        
        if check_existing and not os.path.isfile(db_path):
            raise IOError(f"Path {db_path} does not contain a valid database")
        
        self._path = db_path
        
        return TinyDB(db_path,
                      indent=4,
                      separators=(',', ': '),
                      access_mode=access_mode,
                      storage=CachingMiddleware(
                                            WriteSortMiddleware(JSONStorage)))
    
    def _get_repr(self):
        return f"JSONDataBase records: {len(self)} path: {self._path}"


class MemoryDataBase(DataBase):
    
    def _get_db(self, documents=None):
        
        memdb = TinyDB(storage=MemoryStorage)
        
        if documents is not None:
            memdb.insert_multiple(documents)
        
        return memdb
    
    def _get_repr(self):
        return f"MemoryDataBase records: {len(self)}"


def make_query(path, value=None, exact=False):
    
    query = Query()
    path_resolution = path.strip('/').split('/')
    
    if len(path_resolution) == 1:
        result = query['L0'].any(query.name == path_resolution[0])
    else:
        result = query[f'L{len(path_resolution) - 1}'].any(
                            (query.name == path_resolution[-1]) &
                            (query.parent == '/'.join(path_resolution[:-1])))
    
    if value is not None:
        
        if exact:
            test = lambda value, search: search == value
        else:
            test = lambda value, search: search in value
            
        result &= query[f'L{len(path_resolution) - 1}'].any(
            (query.name == path_resolution[-1]) &
            (query.value.test(test, value)))
    
    return result


def filter_unique_children(db, path):
    
    def check_unique(tree, path):
        
        try:
            node = tree.find_by_path(path)
        except ChildResolverError:
            return False
        
        if len(node.children) == 1: return True
        
        return False
    
    unique_docs = [table.Document(value.to_dict(), doc_id=key)
                       for key, value in db.to_records().items()
                           if check_unique(value, path)]
    
    return MemoryDataBase(unique_docs)


def _order_data(unordered):
    
    def key_sorter(d):
        if "parent" in d:
            return (d["parent"], d["name"])
        if "name" in d:
            return (d["name"], 1)
        return (d, 1)
    
    if isinstance(unordered, (str, ByteString)):
        return unordered
    
    if isinstance(unordered, Sequence):
        return [_order_data(v) for v in natsorted(unordered, key=key_sorter)]
    
    if isinstance(unordered, Mapping):
        return {k: _order_data(v) for k, v in natsorted(unordered.items())}
    
    return unordered


def _get_doc_sorter(path=None, case_insenstive=True):
    
    node_sorter = _get_node_sorter(case_insenstive)
    
    def sorter(doc):
        
        tree = SCHTree.from_dict(dict(doc))
        
        if path is None:
            node = tree.root_node
        else:
            node = tree.find_by_path(path)
        
        return node_sorter(node)
    
    return sorter


def _get_node_sorter(case_insenstive=True):
    
    def sorter(node):
        
        has_value = False
        if hasattr(node, "value"): has_value = True
        
        if case_insenstive:
            name = node.name.lower()
            if has_value: value = node.value.lower()
        else:
            name = node.name
            if has_value: value = node.value
        
        if has_value:
            result = (name, value)
        else:
            result = (name, None)
        
        return result
    
    return sorter


def _is_iterable(obj):
    
    result = False
    excluded_types = (str, dict)
    
    if isinstance(obj, Iterable) and not isinstance(obj, excluded_types):
        result = True
    
    return result
