# -*- coding: utf-8 -*-

import argparse
import datetime

from .arghandler import ArgumentHandler, subcmd

subcommands = {}
subcommands_help = {}
dbcommands = {}
dbcommands_help = {}

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
                        help='Path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='Path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    print(args)

