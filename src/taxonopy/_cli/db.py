# -*- coding: utf-8 -*-

import sys

import inquirer
from inquirer.render.console import ConsoleRender

from . import CLITheme
from .schema import CLIRecordBuilder
from ..schema import SCHTree
from ..db import DataBase


def new_record(schema_path="schema.json",
               db_path="db.json"):
    
    schema = SCHTree.from_json(schema_path)
    db = DataBase(db_path)
    
    builder = CLIRecordBuilder(schema)
    record = None
    
    while True:
        
        record = builder.build(record)
        node = record.root_node
        print(record)
        
        message = f"Store record with {node.name} '{node.value}'?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(
                                                             theme=CLITheme()),
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
                                        render=ConsoleRender(
                                                             theme=CLITheme()),
                                        choices=['yes', 'retry', 'quit'],
                                        default="retry")
            except KeyboardInterrupt:
                sys.exit()
            
            if choice == "quit": return
            if choice == "retry": continue
        
        db.add(record)
        return


def update_records(path,
                   value=None,
                   exact=False,
                   node_path=None,
                   schema_path="schema.json",
                   db_path="db.json"):
    
    schema = SCHTree.from_json(schema_path)
    builder = CLIRecordBuilder(schema)
    db = DataBase(db_path, check_existing=True)
    
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
                                        render=ConsoleRender(theme=CLITheme()),
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
