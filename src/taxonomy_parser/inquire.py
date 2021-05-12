# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:55:45 2021

@author: Work
"""

import inquirer
from anytree import PreOrderIter
from anytree.resolver import ChildResolverError
from blessed import Terminal
from inquirer.render.console import ConsoleRender
from inquirer.themes import Theme

from . import CatTree, get_node_attr, get_node_path, get_parent_path

term = Terminal()

class MyTheme(Theme):
    def __init__(self):
        super(MyTheme, self).__init__()
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


class RecordBuilder:
    
    def __init__(self, schema):
        
        self._schema = schema
        self._iters = [PreOrderIter(schema.root_node, maxlevel=2)]
        self._record = None
        self._render = ConsoleRender(theme=MyTheme())
    
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
        
        node_attr = get_node_attr(node, blacklist=["name"])
        
        # See if node requires data first
        if "type" in node_attr:
            self._select_from_type(node, node_attr)
        
        # Now see if the node is a header for list selection
        if "inquire" in node_attr and node_attr["inquire"] == "list":
            self._select_from_list(node, node_attr)
        
        # Now see if the node is a header for checkbox selection
        if "inquire" in node_attr and node_attr["inquire"] == "check":
            self._select_from_check(node, node_attr)
    
    def _select_from_type(self, node, node_attr):
        
        required = False
        
        if "required" in node_attr: required = bool(node_attr["required"])
        
        message = f"{node.name} [{node.type}]"
        if required: message += " (required)"
        
        while True:
            
            value = inquirer.text(message=message, render=self._render)
            
            if value:
            
                # Check if the type is OK
                val_type = eval(node_attr["type"])
                
                try:
                    val_type(value)
                except:
                    print( "Given value is not compatible with type "
                          f"'{val_type}'" )
                    value = ""
            
            if value or not required: break
        
        if value != "":
            node_attr["value"] = value
        
        self._copy_node_to_record(node, **node_attr)
        
        # If a typed node has no value and no children then we're done
        if "value" not in node_attr or not node.children:
            return
    
    def _select_from_list(self, node, node_attr):
        
        required = False
        node_path = get_node_path(node)
        
        # If not yet added, check if node is required
        try:
            self._record.find_by_path(node_path)
            required = True
        except ChildResolverError:
            if "required" in node_attr and node_attr["required"] == "True":
                required = True
        
        # Ask if the node should be added
        if not required:
            message = f"Add {node.name}?"
            choice = inquirer.list_input(message,
                                         render=self._render,
                                         choices=['yes', 'no'],
                                         default="no")
            
            if choice == "no": return
        
        # Add the parent node if it's not already in the tree
        self._copy_node_to_record(node, **node_attr)
        
        # Gather names of children
        choices = [x.name for x in node.children]
        choice = inquirer.list_input(node.name,
                                     render=self._render,
                                     choices=choices)
        choice_path = f"{node_path}/{choice}"
        
        chosen_node = self._schema.find_by_path(choice_path)
        chosen_node_attr = get_node_attr(chosen_node, blacklist=["name"])
        self._copy_node_to_record(chosen_node, **chosen_node_attr)
        
        if len(chosen_node.children) < 1: return
            
        if "inquire" in chosen_node_attr:
            new_iter = PreOrderIter(chosen_node, maxlevel=1)
        else:
            new_iter = PreOrderIter(chosen_node, maxlevel=2)
            next(new_iter)
        
        self._iters.append(new_iter)

    def _select_from_check(self, node, node_attr):
        
        required = False
        node_path = get_node_path(node)
        
        # Check if required
        if "required" in node_attr and node_attr["required"] == "True":
            required = True
        
        # Prepare message
        if required:
            message = f"{node.name} (select at least one)"
        else:
            message = node.name
        
        while True:
            
            # Gather names of children
            choices = [x.name for x in node.children]
            choices = inquirer.checkbox(message,
                                        render=self._render,
                                        choices=choices)
            
            if not required or len(choices) > 0:
                break
        
        if len(choices) < 1: return
            
        # Add the parent node if it's not already in the tree
        self._copy_node_to_record(node, **node_attr)
        
        chosen_nodes = []
        
        for choice in choices:
            
            chosen_node = self._schema.find_by_name(choice, node_path)
            chosen_node_attr = get_node_attr(chosen_node,
                                             blacklist=["name"])
            
            if len(chosen_node.children) > 0:
                chosen_nodes.append(chosen_node)
            
            self._copy_node_to_record(chosen_node, **chosen_node_attr)
        
        if len(chosen_nodes) < 1: return
            
        new_iter = iter(chosen_node)
        self._iters.append(new_iter)
    
    def _copy_node_to_record(self, node,
                                  **node_attr):
        
        parent_path = get_parent_path(node)
        
        if self._record is None or parent_path is None:
            self._record = CatTree()
            self._record.add_node(node.name, **node_attr)
            return
        
        try:
            node_path = get_node_path(node)
            self._record.find_by_path(node_path)
        except ChildResolverError:
            self._record.add_node(node.name, parent_path, **node_attr)
        
    def __str__(self):
        return self._record.__str__()
