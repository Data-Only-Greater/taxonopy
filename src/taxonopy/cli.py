# -*- coding: utf-8 -*-

import argparse
import datetime

from .arghandler import ArgumentHandler, subcmd


class SmartFormatter(argparse.HelpFormatter):
    
    # https://stackoverflow.com/a/22157136/3215152

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


@subcmd('db', help="database related actions")
def _db(parser,context,topargs):
    
    from db import new_record
    
    parser.formatter_class = SmartFormatter
    parser.add_argument("action",
                        choices=['new'],
                        help="R|Select an action, where\n"
                             "   new = add new record to database")
    parser.add_argument('--path',
                        help='Path to the database (default is ./db.json)',
                        action="store",
                        default="db.json")
    parser.add_argument('--schema',
                        help='Path to the schema (default is ./schema.json)',
                        action="store",
                        default="schema.json")
    
    args = parser.parse_args(topargs)
    
    if args.action == "new":
        new_record(schema_path=args.schema,  db_path=args.path)


def main():
    '''Command line interface for manipulating records stored with taxonopy.
    
    Example:
    
        To get help::
            
            $ taxonopy -h
    
    '''
    
    now = datetime.datetime.now()
    epiStr = 'Data Only Greater (C) {}.'.format(now.year)
    desStr = ("Command line interface for taxonopy")
    
    handler = ArgumentHandler(description=desStr,
                              epilog=epiStr,
                              use_subcommand_help=True)
    handler.run()
