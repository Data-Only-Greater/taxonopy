# -*- coding: utf-8 -*-

import inquirer
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
    
    def count(self, node_path, value=None):
        return self._db.count(_make_query(node_path, value))
    
    def add(self, record):
        self._db.insert(record.to_dict())
    
    def replace(self, doc_id, record):
        self._db.remove(doc_ids=[doc_id])
        self._db.insert(table.Document(record.to_dict(), doc_id=doc_id))


def new_record(schema_path="schema.json",
               db_path="db.json"):
    
    schema = SCHTree()
    schema.from_json(schema_path)
    db = DataBase(db_path)
    
    builder = RecordBuilder(schema)
    record = None
    
    while True:
        
        record = builder.build(record)
        node = record.find_by_path("Title")
        print(record)
        
        message = f"Store record with title '{node.value}'?"
        choice = inquirer.list_input(message,
                                     render=ConsoleRender(theme=MyTheme()),
                                     choices=['yes', 'retry', 'quit'],
                                     default="yes")
        
        if choice == "quit": return
        if choice == "retry": continue
        
        count = db.count("Title", node.value)
        
        if count > 0:
            
            message = (f"A record with title '{node.value}' already exists. "
                        "Add another?")
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(theme=MyTheme()),
                                         choices=['yes', 'retry', 'quit'],
                                         default="retry")
            
            if choice == "quit": return
            if choice == "retry": continue
        
        db.add(record)
        return


def _make_query(path, value=None):
    
    query = Query()
    path_resolution = path.strip('/').split('/')
    result = query['L0'].exists()
    
    for i, path in enumerate(path_resolution):
        result &= query[f'L{i}'].any(query.name == path)
    
    if value is not None:
        result &= query[f'L{len(path_resolution) - 1}'].any(
                                                        query.value == value)
    
    return result
