# -*- coding: utf-8 -*-

import sys
import textwrap

import inquirer
from inquirer.render.console import ConsoleRender

from . import CLITheme
from .schema import CLIRecordBuilder
from ..db import _is_iterable, make_query
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
            db.insert(record)
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
    
    query = make_query(path, value, exact)
    memdb = db.search(query)
    
    for doc_id, record in memdb.to_records().items():
        
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


def show_nodes(paths, db, max_col_width=50):
    
    def _get_msg(attrs):
        
        if not attrs: return None
        
        key = f"{attrs['name']}"
        
        if "value" in attrs:
            value = f"{attrs['value']}"
            return (key, value)
        
        if "inquire" in attrs:
            value = ", ".join(attrs['children'])
            return (key, value)
        
        return None
    
    if not _is_iterable(paths):
        paths = (paths,)
    
    records = db.projection(paths)
    msg_rows = []
    
    for record in zip(*records.values()):
        
        msgs = []
        
        for i, _ in enumerate(paths):
            msgs.append(_get_msg(record[i+1]))
        
        if set(msgs) == set([None]):
            continue
        
        msg_rows.append(msgs)
    
    # Remove columns with no msgs
    transpose = lambda x: list(map(list, zip(*x)))
    msg_cols = transpose(msg_rows)
    msg_cols = [msgs for msgs in msg_cols if set(msgs) != set([None])]
    msg_rows = transpose(msg_cols)
    
    if not msg_rows: return
    
    def msg_width(x):
        if x is None: return 0
        return len(x[0]) + len(x[1]) + 2
    
    widths = [msg_width(max(msgs, key=msg_width)) + 1
                                              for msgs in zip(*msg_rows)]
    widths = [x if x < max_col_width else max_col_width for x in widths]
    
    for msgs in msg_rows:
        
        wrapped_msgs = []
        
        for msg in msgs:
            
            if msg is None:
                wrapped = []
            else:
                wrapped = textwrap.wrap(msg[1],
                                        max_col_width - (len(msg[0]) + 2))
            
            wrapped_msgs.append(wrapped)
        
        total_lines = len(max(wrapped_msgs))
        
        for j in range(total_lines):
            
            final_str = ""
            
            for i, (msg, wrapped_msg, width) in enumerate(zip(msgs,
                                                              wrapped_msgs,
                                                              widths)):
                
                if msg is None:
                    msg = ""
                elif j == 0:
                    msg = f'{msg[0]}: {wrapped_msg[0]}'
                elif j >= len(wrapped_msg):
                    msg = ""
                else:
                    msg = f'{" " * (len(msg[0]) + 2)}{wrapped_msg[j]}'
                
                final_str += f'{msg: <{width}}'
                if i < len(widths) - 1: final_str += "| "
            
            print(final_str)
