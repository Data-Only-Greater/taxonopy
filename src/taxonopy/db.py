# -*- coding: utf-8 -*-

import sys
import itertools
from collections import OrderedDict
from collections.abc import Iterable

import inquirer
from anytree.resolver import ChildResolverError
from inquirer.render.console import ConsoleRender
from tinydb import table, TinyDB, Query

from .tree import SCHTree
from .inquire import MyTheme, RecordBuilder


class DataBase:
    
    def __init__(self, db_path="db.json"):
        self._db = TinyDB(db_path,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
    
    def add(self, record):
        self._db.insert(record.to_dict())
    
    def all(self):
        sorter = _get_doc_sorter()
        return OrderedDict((doc.doc_id, SCHTree.from_dict(dict(doc)))
                                   for doc in sorted(self._db, key=sorter))
    
    def count(self, node_path, value=None):
        return self._db.count(_make_query(node_path, value))
    
    def get(self, node_path, value=None, exact=False):
        query = _make_query(node_path, value, exact)
        sorter = _get_doc_sorter()
        return OrderedDict((doc.doc_id, SCHTree.from_dict(dict(doc)))
                       for doc in sorted(self._db.search(query), key=sorter))
    
    def replace(self, doc_id, record):
        self._db.remove(doc_ids=[doc_id])
        self._db.insert(table.Document(record.to_dict(), doc_id=doc_id))


def new_record(schema_path="schema.json",
               db_path="db.json"):
    
    schema = SCHTree.from_json(schema_path)
    db = DataBase(db_path)
    
    builder = RecordBuilder(schema)
    record = None
    
    while True:
        
        record = builder.build(record)
        node = record.root_node
        print(record)
        
        message = f"Store record with {node.name} '{node.value}'?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(theme=MyTheme()),
                                         choices=['yes', 'retry', 'quit'],
                                         default="yes")
        except KeyboardInterrupt:
            sys.exit()
        
        if choice == "quit": return
        if choice == "retry": continue
        
        count = db.count(f"{node.name}", node.value)
        
        if count > 0:
            
            message = (f"A record with {node.name} '{node.value}' already "
                        "exists. Add another?")
            
            try:
                choice = inquirer.list_input(
                                        message,
                                        render=ConsoleRender(theme=MyTheme()),
                                        choices=['yes', 'retry', 'quit'],
                                        default="retry")
            except KeyboardInterrupt:
                sys.exit()
            
            if choice == "quit": return
            if choice == "retry": continue
        
        db.add(record)
        return


def show_count(path,
               value=None,
               db_path="db.json"):
    db = DataBase(db_path)
    count = db.count(path, value)
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
    db = DataBase(db_path)
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
        
        filtered_msgs = tuple(x for x in msgs if x)
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
    db = DataBase(db_path)
    for record in db.get(path, value, exact).values(): print(record)


def update_records(path,
                   value=None,
                   exact=False,
                   node_path=None,
                   schema_path="schema.json",
                   db_path="db.json"):
    
    schema = SCHTree.from_json(schema_path)
    builder = RecordBuilder(schema)
    db = DataBase(db_path)
    
    for doc_id, record in db.get(path, value, exact).items():
        
        node = record.root_node
        message = f"Update record with {node.name} '{node.value}'?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(theme=MyTheme()),
                                         choices=['yes', 'no', 'quit'],
                                         default="yes")
        except KeyboardInterrupt:
                sys.exit()
            
        if choice == "quit": return
        if choice == "no": continue
        
        while True:
            
            updated = builder.build(record, node_path)
            print(updated)
            
            message = "Store updated record?"
            
            try:
                choice = inquirer.list_input(
                                        message,
                                        render=ConsoleRender(theme=MyTheme()),
                                        choices=['yes',
                                                 'no',
                                                 'retry',
                                                 'quit'],
                                        default="yes")
            except KeyboardInterrupt:
                sys.exit()
            
            if choice == "quit": return
            if choice == "retry": continue
            if choice == "no": break
            
            db.replace(doc_id, updated)
            break


def _make_query(path, value=None, exact=False):
    
    query = Query()
    path_resolution = path.strip('/').split('/')
    result = query['L0'].exists()
    
    for i, path in enumerate(path_resolution):
        result &= query[f'L{i}'].any(query.name == path)
    
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
