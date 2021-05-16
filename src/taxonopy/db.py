# -*- coding: utf-8 -*-

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
        return {doc.doc_id: SCHTree.from_dict(dict(doc)) for doc in self._db}
    
    def count(self, node_path, value=None):
        return self._db.count(_make_query(node_path, value))
    
    def get(self, node_path, value=None, exact=False):
        query = _make_query(node_path, value, exact)
        return {doc.doc_id: SCHTree.from_dict(dict(doc))
                                        for doc in self._db.search(query)}
    
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
        choice = inquirer.list_input(message,
                                     render=ConsoleRender(theme=MyTheme()),
                                     choices=['yes', 'retry', 'quit'],
                                     default="yes")
        
        if choice == "quit": return
        if choice == "retry": continue
        
        count = db.count(f"{node.name}", node.value)
        
        if count > 0:
            
            message = (f"A record with {node.name} '{node.value}' already "
                        "exists. Add another?")
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(theme=MyTheme()),
                                         choices=['yes', 'retry', 'quit'],
                                         default="retry")
            
            if choice == "quit": return
            if choice == "retry": continue
        
        db.add(record)
        return

def show_nodes(path=None, db_path="db.json"):
    
    db = DataBase(db_path)
    records = db.all()
    
    for record in records.values():
        
        if path is None:
            node = record.root_node
        else:
            
            try: 
                node = record.find_by_path(path)
            except ChildResolverError:
                continue
        
        msg_str = f"{node.name}"
        if hasattr(node, "value"): msg_str += f": {node.value}"
        print(msg_str)


def show_records(path, value=None, exact=False, db_path="db.json"):
    db = DataBase(db_path)
    for record in db.get(path, value, exact).values(): print(record)


def update_records(path,
                   value=None,
                   exact=False,
                   schema_path="schema.json",
                   db_path="db.json"):
    
    schema = SCHTree.from_json(schema_path)
    builder = RecordBuilder(schema)
    db = DataBase(db_path)
    
    for doc_id, record in db.get(path, value, exact).items():
        
        node = record.root_node
        message = f"Update record with {node.name} '{node.value}'?"
        choice = inquirer.list_input(message,
                                     render=ConsoleRender(theme=MyTheme()),
                                     choices=['yes', 'no', 'quit'],
                                     default="yes")
            
        if choice == "quit": return
        if choice == "no": continue
        
        while True:
            
            updated = builder.build(record)
            print(updated)
            
            message = "Store updated record?"
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(theme=MyTheme()),
                                         choices=['yes', 'retry', 'quit'],
                                         default="yes")
            
            if choice == "quit": return
            if choice == "retry": continue
            
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
