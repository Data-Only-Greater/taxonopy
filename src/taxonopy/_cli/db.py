# -*- coding: utf-8 -*-

import sys

import inquirer
from inquirer.render.console import ConsoleRender

from . import CLITheme
from .schema import CLIRecordBuilder
from ..schema import SCHTree
from ..db import DataBase
from ..utils import get_root_value_ids


def new_record(schema, db):
    
    root_value_ids = get_root_value_ids(db)
    
    builder = CLIRecordBuilder(schema)
    record = None
    doc_id = None
    
    while True:
        
        try:
            record = builder.build(record)
        except KeyboardInterrupt:
            db.close()
            sys.exit()
        
        node = record.root_node
        print(record)
        
        if node.value in root_value_ids:
            message = "Replace "
            doc_id = root_value_ids[node.value]
        else:
            message = "Store "
        
        message += f"record with {node.name} '{node.value}'?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(
                                                             theme=CLITheme()),
                                         choices=['yes', 'retry', 'quit'],
                                         default="yes")
        except KeyboardInterrupt:
            db.close()
            sys.exit()
        
        if choice == "quit": return
        if choice == "retry": continue
        
        if doc_id is None:
            db.add(record)
        else:
            db.replace(doc_id, record)
        
        db.close()
        
        return


def update_records(path,
                   schema,
                   db,
                   value=None,
                   exact=False,
                   node_path=None):
    
    builder = CLIRecordBuilder(schema)
    
    for doc_id, record in db.get(path, value, exact).items():
        
        node = record.root_node
        message = f"Update record with {node.name} '{node.value}'?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(
                                                             theme=CLITheme()),
                                         choices=['yes', 'no', 'quit'],
                                         default="yes")
        except KeyboardInterrupt:
            db.close()
            sys.exit()
            
        if choice == "quit": return
        if choice == "no": continue
        
        while True:
            
            try:
                updated = builder.build(record, node_path)
            except KeyboardInterrupt:
                db.close()
                sys.exit()
            
            print(updated)
            
            message = "Store updated record?"
            
            try:
                choice = inquirer.list_input(
                                        message,
                                        render=ConsoleRender(theme=CLITheme()),
                                        choices=['yes',
                                                 'no',
                                                 'retry',
                                                 'quit'],
                                        default="yes")
            except KeyboardInterrupt:
                db.close()
                sys.exit()
            
            if choice == "quit": return
            if choice == "retry": continue
            if choice == "no": break
            
            db.replace(doc_id, updated)
            break
    
    db.close()
