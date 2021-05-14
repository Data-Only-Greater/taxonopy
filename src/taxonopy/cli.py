# -*- coding: utf-8 -*-

import argparse
import datetime

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


@subcmd('new',
        dbcommands,
        dbcommands_help,
        help="add new record")
def _db_new(parser,context,topargs):
    
    parser.add_argument('--path',
                        help='path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    from .db import new_record
    new_record(args.schema, args.path)


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
