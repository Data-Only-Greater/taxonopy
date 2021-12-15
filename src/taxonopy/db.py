# -*- coding: utf-8 -*-

import os
import itertools
from collections import OrderedDict
from collections.abc import ByteString, Iterable, Mapping, Sequence

from anytree.resolver import ChildResolverError
from natsort import natsorted
from tinydb import table, TinyDB, Query
from tinydb.middlewares import Middleware
from tinydb.storages import JSONStorage

from .schema import SCHTree


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


class DataBase:
    
    def __init__(self, db_path="db.json",
                       check_existing=False,
                       access_mode='r+'):
        
        if check_existing and not os.path.isfile(db_path):
            raise IOError(f"Path {db_path} does not contain a valid database")
        
        self._db = TinyDB(db_path,
                          indent=4,
                          separators=(',', ': '),
                          access_mode=access_mode,
                          storage=WriteSortMiddleware(JSONStorage))
    
    def __enter__(self):
        self._db.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._db.__exit__(exc_type, exc_val, exc_tb)
    
    def close(self):
        self._db.close()
    
    def add(self, record):
        self._db.insert(record.to_dict())
    
    def all(self):
        sorter = _get_doc_sorter()
        return OrderedDict((doc.doc_id, SCHTree.from_dict(dict(doc)))
                                   for doc in sorted(self._db, key=sorter))
    
    def count(self, node_path, value=None, exact=False, inverse=False):
        
        query = _make_query(node_path, value, exact)
        
        if inverse:
            result = self._db.count(~query)
        else:
            result = self._db.count(query)
        
        return result
    
    def flush(self):
        null = lambda x: x
        self._db._update_table(null)
    
    def get(self, node_path, value=None, exact=False):
        query = _make_query(node_path, value, exact)
        sorter = _get_doc_sorter()
        return OrderedDict((doc.doc_id, SCHTree.from_dict(dict(doc)))
                       for doc in sorted(self._db.search(query), key=sorter))
    
    def replace(self, doc_id, record):
        self._db.remove(doc_ids=[doc_id])
        self._db.insert(table.Document(record.to_dict(), doc_id=doc_id))


def show_count(path,
               value=None,
               exact=False,
               db_path="db.json"):
    db = DataBase(db_path, check_existing=True)
    count = db.count(path, value, exact)
    msg = f"{path}: {count}"
    print(msg)


def show_nodes(paths=None, db_path="db.json"):
    
    def _get_msg(node):
        
        msg_str = f"{node.name}"
        
        if hasattr(node, "value"):
            msg_str += f": {node.value}"
            return msg_str
            
        if hasattr(node, "inquire"):
            
            child_names = []
            sorter = _get_node_sorter()
            
            for child in sorted(node.children, key=sorter):
                child_names.append(child.name)
            
            child_str = ", ".join(child_names)
            
            if len(child_names) == 1:
                msg_str += f": {child_str}"
            elif len(child_names) > 1:
                msg_str += ": {" + child_str + "}"
            
            return msg_str
        
        return msg_str
    
    multi_field = False
    
    if not _is_iterable(paths):
        paths = (paths,)
    
    if len(paths) > 2: multi_field = True
    db = DataBase(db_path, check_existing=True)
    records = db.all()
    
    msg_rows = []
    
    for record in records.values():
        
        msgs = []
        
        for path in paths:
            
            if path is None:
                node = record.root_node
            else:
                try: 
                    node = record.find_by_path(path)
                except ChildResolverError:
                    msgs.append(False)
                    continue
            
            msgs.append(_get_msg(node))
        
        if not multi_field:
            if all(msgs): msg_rows.append(msgs)
            continue
        
        filtered_msgs = tuple(x if x else "" for x in msgs )
        if len(filtered_msgs) < 2: continue
        msg_rows.append(filtered_msgs)
    
    widths = [len(max(msgs, key=len)) + 1
                  for msgs in itertools.zip_longest(*msg_rows, fillvalue="")]
    
    for x in msg_rows:
        
        final_str = ""
        
        for i, msg in enumerate(x):
            final_str += f'{msg: <{widths[i]}}'
            if i < len(widths) - 1: final_str += "| "
        
        print(final_str)


def show_records(path, value=None, exact=False, db_path="db.json"):
    db = DataBase(db_path, check_existing=True)
    for record in db.get(path, value, exact).values(): print(record)


def _order_data(unordered):
    
    def key_sorter(d):
        if "parent" in d:
            return (d["parent"], d["name"])
        return (d["name"], 1)
    
    if isinstance(unordered, (str, ByteString)):
        return unordered
    
    if isinstance(unordered, Sequence):
        return [_order_data(v) for v in natsorted(unordered, key=key_sorter)]
    
    if isinstance(unordered, Mapping):
        return {k: _order_data(v) for k, v in natsorted(unordered.items())}
    
    return unordered


def _make_query(path, value=None, exact=False):
    
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
                                            query.value.test(test, value))
    
    return result


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
            result = name
        
        return result
    
    return sorter


def _is_iterable(obj):
    
    result = False
    excluded_types = (str, dict)
    
    if isinstance(obj, Iterable) and not isinstance(obj, excluded_types):
        result = True
    
    return result
