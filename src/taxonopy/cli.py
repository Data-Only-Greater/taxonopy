# -*- coding: utf-8 -*-

import argparse
import datetime
from anytree.resolver import ChildResolverError

from .arghandler import ArgumentHandler, parse_vars, subcmd

subcommands = {}
subcommands_help = {}
dbcommands = {}
dbcommands_help = {}
schemacommands = {}
schemacommands_help = {}

### MAIN

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
    handler.run()

### DATABASE

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
    parser.add_argument('--db',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    
    args = parser.parse_args(topargs)
    
    from .db import show_count
    show_count(args.path, args.value, args.db)


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
    
    from .db import show_nodes
    show_nodes(args.path, args.db)


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
    
    from .db import show_records
    show_records(args.path, args.value, args.exact, args.db)


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
    update_records(args.path,
                   args.value,
                   args.exact,
                   args.field,
                   args.schema,
                   args.db)


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
    
    from .db import dump_xl
    dump_xl(args.path, args.schema, args.db)


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
    
    args = parser.parse_args(topargs)
    
    from .db import load_xl
    load_xl(args.db_path, args.xl_path, args.schema, args.append)

### SCHEMA

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
    
    from .tree import SCHTree
    schema = SCHTree.from_json(args.schema)
    
    print(schema)


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
    
    from .tree import SCHTree
    
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
    
    from .tree import SCHTree
    
    schema = SCHTree.from_json(args.schema)
    schema.delete_node(args.path)
    
    print(schema)
    
    if args.dry_run: return
    schema.to_json(out)
