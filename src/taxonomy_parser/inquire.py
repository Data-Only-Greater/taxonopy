# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:55:45 2021

@author: Work
"""

import inquirer
from anytree import PreOrderIter
from anytree.resolver import ChildResolverError

from . import CatTree, get_node_attr, get_node_path, get_parent_path

class RecordBuilder:
    
    def __init__(self, schema):
        
        self._schema = schema
        self._iters = [PreOrderIter(schema.root_node, maxlevel=2)]
        self._record = None
    
    def next(self):
        
        top_iter = self._iters[-1]
        
        while True:
            
            try:
                node = next(top_iter)
                break
            except StopIteration:
                self._iters.pop()
                if len(self._iters) == 0:
                    raise StopIteration
                top_iter = self._iters[-1]
        
        node_path = get_node_path(node)
        node_attr = get_node_attr(node, blacklist=["name"])
        
        # See if node requires data first
        if "type" in node_attr:
            
            message = f"{node.name} ({node.type})"
            required = False
            if "required" in node_attr: required = node_attr["required"]
            
            while True:
                value = inquirer.text(message=message)
                break
                if value or not required: break
            
            if value != "":
                node_attr["value"] = value
            
            if self._record is None:
                
                self._record = CatTree()
                self._record.add_node(node.name, **node_attr)
                print(self._record)
        
            # If a typed node has no value and no children then we're done
            if "value" not in node_attr or not node.children:
                return
        
        else:
            
            # Add the node if it's not already in the tree
            try:
                self._record.find_by_path(node_path)
            except ChildResolverError:
                parent_path = get_parent_path(node)
                self._record.add_node(node.name, parent_path, **node_attr)
                print(self._record)
        
        # Now see if the node is a header for list selection
        if "inquire" in node_attr and node_attr["inquire"] == "list":
            
            # Gather names of children
            choices = [x.name for x in node.children]
            choice = inquirer.list_input(node.name, choices=choices)
            
            chosen_node = self._schema.find_by_name(choice, node_path)
            chosen_node_attr = get_node_attr(chosen_node, blacklist=["name"])
            
            self._record.add_node(choice, node_path, **chosen_node_attr)
            
            print(self._record)
            
            if len(chosen_node.children) > 0:
                
                if "inquire" in chosen_node_attr:
                    new_iter = PreOrderIter(chosen_node, maxlevel=1)
                else:
                    new_iter = PreOrderIter(chosen_node, maxlevel=2)
                    next(new_iter)
                
                self._iters.append(new_iter)
        
        # Now see if the node is a header for checkbox selection
        if "inquire" in node_attr and node_attr["inquire"] == "check":
            
            # Gather names of children
            choices = [x.name for x in node.children]
            choices = inquirer.checkbox(node.name, choices=choices)
            
            chosen_nodes = []
            
            for choice in choices:
                
                chosen_node = self._schema.find_by_name(choice, node_path)
                chosen_node_attr = get_node_attr(chosen_node,
                                                 blacklist=["name"])
                
                if len(chosen_node.children) > 0:
                    chosen_nodes.append(chosen_node)
                
                self._record.add_node(choice, node_path, **chosen_node_attr)
            
            print(self._record)
            
            if len(chosen_nodes) > 0:
                new_iter = iter(chosen_node)
                self._iters.append(new_iter)
