# -*- coding: utf-8 -*-

import os
import csv
import sys
import argparse
import datetime

import inquirer
from blessed import Terminal
from anytree.resolver import ChildResolverError
from inquirer.themes import Theme
from inquirer.render.console import ConsoleRender

from .arghandler import ArgumentHandler, parse_vars, subcmd


### CLI FORMATTING

term = Terminal()

class CLITheme(Theme):
    def __init__(self):
        super(CLITheme, self).__init__()
        self.Question.mark_color = term.yellow
        self.Question.brackets_color = term.bright_green
        self.Question.default_color = term.yellow
        self.Checkbox.selection_color = term.bright_green
        self.Checkbox.selection_icon = ">"
        self.Checkbox.selected_icon = "X"
        self.Checkbox.selected_color = term.yellow + term.bold
        self.Checkbox.unselected_color = term.normal
        self.Checkbox.unselected_icon = "o"
        self.List.selection_color = term.bright_green
        self.List.selection_cursor = ">"
        self.List.unselected_color = term.normal

### MAIN CLI

subcommands = {}
subcommands_help = {}

def main():
    '''Command line interface for taxonopy.
    
    Example:
    
        To get help::
            
            $ taxonopy -h
    
    '''
    
    now = datetime.datetime.now()
    desStr = ("Command line interface for taxonopy")
    epiStr = 'Data Only Greater (C) {}.'.format(now.year)
    
    handler = ArgumentHandler(description=desStr,
                              epilog=epiStr,
                              use_subcommand_help=True,
                              registered_subcommands=subcommands,
                              registered_subcommands_help=subcommands_help)
    
    handler.add_argument('-v', '--version',
                        help='print version and exit',
                        action="store_true")
    
    # Handle -v or --version using sys.argv
    if _print_version(): return
    
    # Handle remaining args
    handler.run()


def _print_version():
    
    if len(sys.argv) == 1: return False
    if set(sys.argv[1:]) & set(['-h', '--help']): return False
    
    test_arg = sys.argv[1]
    should_exit = False
    
    if test_arg in ['-v', '--version']:
        from . import get_name, get_version
        print(f"{get_name()} {get_version()}")
        should_exit = True
    
    return should_exit



### DATABASE CLI

dbcommands = {}
dbcommands_help = {}

@subcmd('db',
        subcommands,
        subcommands_help,
        help="database related actions")
def _db(parser,context,topargs):
    handler = ArgumentHandler(use_subcommand_help=True,
                              registered_subcommands=dbcommands,
                              registered_subcommands_help=dbcommands_help)
    handler.prog = "taxonopy db"
    handler.run(topargs)


@subcmd('new',
        dbcommands,
        dbcommands_help,
        help="add new record")
def _db_new(parser,context,topargs):
    
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    from .db import new_record
    new_record(args.schema, args.db)


@subcmd('update',
        dbcommands,
        dbcommands_help,
        help="update existing records")
def _db_update(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of field to search',
                        action="store")
    parser.add_argument('--value',
                        help='only show records with matching field value',
                        action="store")
    parser.add_argument('--exact',
                        help='only show exact value matches',
                        action="store_true")
    parser.add_argument('--field',
                        help='only update the given field',
                        action="store")
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    from .db import update_records
    
    try:
        update_records(args.path,
                       args.value,
                       args.exact,
                       args.field,
                       args.schema,
                       args.db)
    except IOError:
        print("Database not found")


@subcmd('count',
        dbcommands,
        dbcommands_help,
        help="count records")
def _db_count(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of field to count',
                        action='store')
    parser.add_argument('--value',
                        help='only matching given value',
                        action="store")
    parser.add_argument('--exact',
                        help='only show exact value matches',
                        action="store_true")
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    
    args = parser.parse_args(topargs)
    
    from ..db import show_count
    
    try:
        show_count(args.path, args.value, args.exact, args.db)
    except IOError:
        print("Database not found")


@subcmd('choices',
        dbcommands,
        dbcommands_help,
        help="show count for fields with choices")
def _db_choices(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of field to count',
                        action='store')
    parser.add_argument('--csv',
                        help='save results to csv file at given path',
                        action="store")
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    from ..utils import choice_count
    
    try:
        count = choice_count(args.path, args.db, args.schema)
    except IOError:
        print("Database not found")
    
    msg = (f"{k}: {v}" for k, v in count.items())
    print('\n'.join(msg))
    
    if args.csv is None: return
    
    with open(args.csv, 'w', newline='') as csvfile:
        
        writer = csv.writer(csvfile,
                            delimiter=',',
                            quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Field", "Count"])
        
        for k, v in count.items():
            writer.writerow([k, v])


@subcmd('show',
        dbcommands,
        dbcommands_help,
        help="show full records")
def _db_show(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of field to search',
                        action="store")
    parser.add_argument('--value',
                        help='only show records with matching field value',
                        action="store")
    parser.add_argument('--exact',
                        help='only show exact value matches',
                        action="store_true")
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    
    args = parser.parse_args(topargs)
    
    from ..db import show_records
    
    try:
        show_records(args.path, args.value, args.exact, args.db)
    except IOError:
        print("Database not found")


@subcmd('list',
        dbcommands,
        dbcommands_help,
        help="list node for all records")
def _db_list(parser,context,topargs):
    
    parser.add_argument('--path',
                        help='path of field to display (default is root)',
                        action='append')
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    
    args = parser.parse_args(topargs)
    
    from ..db import show_nodes
    
    try:
        show_nodes(args.path, args.db)
    except IOError:
        print("Database not found")


@subcmd('dump',
        dbcommands,
        dbcommands_help,
        help="dump database to excel")
def _db_dump(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of xlsx file to create',
                        action="store")
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    from ..utils import dump_xl
    
    try:
        dump_xl(args.path, args.schema, args.db)
    except IOError:
        print("Database not found")


@subcmd('load',
        dbcommands,
        dbcommands_help,
        help="load database from excel")
def _db_load(parser,context,topargs):
    
    parser.add_argument('db_path',
                        help='path to the database file to fill',
                        action="store")
    parser.add_argument('xl_path',
                        help='path of xlsx file to read',
                        action="store")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    parser.add_argument('--append',
                        help=('append to an existing database (otherwise '
                              'overwritten)'),
                        action="store_true")
    parser.add_argument('--strict',
                        help=('values must conform to the schema'),
                        action="store_true")
    
    args = parser.parse_args(topargs)
    
    from ..utils import load_xl
    load_xl(args.db_path, args.xl_path, args.schema, args.append, args.strict)

### SCHEMA CLI

schemacommands = {}
schemacommands_help = {}

@subcmd('schema',
        subcommands,
        subcommands_help,
        help="schema related actions")
def _schema(parser,context,topargs):
    handler = ArgumentHandler(use_subcommand_help=True,
                              registered_subcommands=schemacommands,
                              registered_subcommands_help=schemacommands_help)
    handler.prog = "taxonopy schema"
    handler.run(topargs)


@subcmd('show',
        schemacommands,
        schemacommands_help,
        help="view the schema")
def _schema_show(parser,context,topargs):
    
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    if not os.path.isfile(args.schema): return
    
    from ..schema import SCHTree
    schema = SCHTree.from_json(args.schema)
    print(schema)


@subcmd('new',
        schemacommands,
        schemacommands_help,
        help="create the root field in a new schema")
def _schema_new(parser,context,topargs):
    
    parser.add_argument('name',
                        help='name of the root field',
                        action="store")
    parser.add_argument("--attributes",
                        metavar="KEY=VALUE",
                        nargs='+',
                        help="set field attributes as key-value pairs "
                             "(do not put spaces before or after the = sign). "
                             "If a value contains spaces, you should define "
                             "it with double quotes: "
                             'foo="this is a sentence". Note that '
                             "values are always treated as strings. "
                             "(pre-added: 'type=str required=True'). ")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    parser.add_argument('--dry-run',
                        help=('show new schema without saving'),
                        action="store_true")
    
    args = parser.parse_args(topargs)
    
    if os.path.isfile(args.schema):
        
        message = f"A schema already exists at path {args.schema}. Overwrite?"
        
        try:
            choice = inquirer.list_input(message,
                                         render=ConsoleRender(
                                                             theme=CLITheme()),
                                         choices=['yes', 'no'],
                                         default='no')
        except KeyboardInterrupt:
                sys.exit()
        
        if choice == "no": return
        
    from ..schema import SCHTree
    
    node_attr = parse_vars(args.attributes)
    if "type" not in node_attr: node_attr["type"] = "str"
    if "required" not in node_attr: node_attr["required"] = "True"
    
    schema = SCHTree()
    schema.add_node(args.name, **node_attr)
    
    print(schema)
    
    if args.dry_run: return
    schema.to_json(args.schema)


@subcmd('add',
        schemacommands,
        schemacommands_help,
        help="add (or replace) field in the schema")
def _schema_add(parser,context,topargs):
    
    parser.add_argument('name',
                        help='name of the field to add',
                        action="store")
    parser.add_argument('parent',
                        help='path to parent field',
                        action="store")
    parser.add_argument("--attributes",
                        metavar="KEY=VALUE",
                        nargs='+',
                        help="set field attributes as key-value pairs "
                             "(do not put spaces before or after the = sign). "
                             "If a value contains spaces, you should define "
                             "it with double quotes: "
                             'foo="this is a sentence". Note that '
                             "values are always treated as strings.")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    parser.add_argument('-o', '--out',
                        help=('output path for the schema (default is to '
                              'overwrite)'),
                        action="store")
    parser.add_argument('--dry-run',
                        help=('show new schema without saving'),
                        action="store_true")
    
    args = parser.parse_args(topargs)
    
    if args.out is not None:
        out = args.out
    else:
        out = args.schema
    
    node_attr = parse_vars(args.attributes)
    
    from ..schema import SCHTree
    
    schema = SCHTree.from_json(args.schema)
    total_path = f"{args.parent}/{args.name}"
    
    try: 
        node = schema.find_by_path(total_path)
        node.parent = None
    except ChildResolverError:
        pass
    
    schema.add_node(args.name, args.parent, **node_attr)
    
    print(schema)
    
    if args.dry_run: return
    schema.to_json(out)


@subcmd('delete',
        schemacommands,
        schemacommands_help,
        help="delete field from the schema")
def _schema_delete(parser,context,topargs):
    
    parser.add_argument('path',
                        help='path of field to delete',
                        action="store")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    parser.add_argument('-o', '--out',
                        help=('output path for the schema (default is to '
                              'overwrite)'),
                        action="store")
    parser.add_argument('--dry-run',
                        help=('show new schema without saving'),
                        action="store_true")
    
    args = parser.parse_args(topargs)
    
    if args.out is not None:
        out = args.out
    else:
        out = args.schema
    
    from ..schema import SCHTree
    
    schema = SCHTree.from_json(args.schema)
    schema.delete_node(args.path)
    
    print(schema)
    
    if args.dry_run: return
    schema.to_json(out)
