# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:55:45 2021

@author: Work
"""

import re
import sys
import importlib
from abc import ABC, abstractmethod

import inquirer
from anytree import PreOrderIter
from anytree.resolver import ChildResolverError
from blessed import Terminal
from inquirer.render.console import ConsoleRender
from inquirer.themes import Theme

from .tree import SCHTree, get_node_attr, get_node_path, get_parent_path

term = Terminal()


class RecordBuilderBase(ABC):

    def __init__(self, schema):
        
        self._schema = schema
        self._iters = None
    
    @abstractmethod
    def build(self, existing=None):
        return
    
    def _build(self, record, existing=None):
        
        while True:
            try:
                self._next(record, existing)
            except StopIteration:
                break
        
        self._iters = None
        
        return record
    
    def _next(self, record, existing=None):
        
        try:
            top_iter = self._iters[-1]
        except IndexError:
            raise StopIteration
        
        while True:
            
            try:
                node = next(top_iter)
                break
            except StopIteration:
                self._iters.pop()
                if len(self._iters) == 0:
                    raise StopIteration
                top_iter = self._iters[-1]
        
        self._build_node(record, node, existing)
    
    @abstractmethod
    def _build_node(record, node, existing=None):
        return


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


class CLIRecordBuilder(RecordBuilderBase):
    
    def __init__(self, schema):
        super().__init__(schema)
        self._render = ConsoleRender(theme=CLITheme())
    
    def build(self, existing=None, node_path=None):
        
        # Update just one node in an existing record
        if existing is not None and node_path is not None:
            
            self._iters = []
            record = SCHTree.from_dict(existing.to_dict())
            children = None
            
            try:
                old_node = record.find_by_path(node_path)
                children = old_node.children
                record.delete_node(node_path)
            except ChildResolverError:
                pass
            
            node = self._schema.find_by_path(node_path)
            self._build_node(record, node, existing, children)
        
        else:
            
            self._iters = [iter([self._schema.root_node])]
            record = SCHTree()
        
        record = self._build(record, existing)
        
        return record
    
    def _build_node(self, record, node, existing=None, children=None):
        
        node_attr = get_node_attr(node, blacklist=["name"])
        
        # See if node requires data first
        if "type" in node_attr:
            
            if children is not None: node_attr["children"] = children
            self._select_from_type(record, node, node_attr, existing)
            
            # If a typed node has no value and no children then we're done
            if "value" not in node_attr or not node.children:
                return
        
        # Now see if the node is a header for list selection
        if "inquire" in node_attr and node_attr["inquire"] == "list":
            self._select_from_list(record, node, node_attr, existing)
            return
        
        # Now see if the node is a header for checkbox selection
        if "inquire" in node_attr and node_attr["inquire"] == "checkbox":
            self._select_from_check(record, node, node_attr, existing)
            return
        
        if children is not None: node_attr["children"] = children
        _copy_node_to_record(record, node, **node_attr)
        
        if len(node.children) < 1: return
        
        new_iter = PreOrderIter(node, maxlevel=2)
        next(new_iter)
        
        self._iters.append(new_iter)
    
    def _select_from_type(self, record, node, node_attr, existing=None):
        if self._set_node_type(node, node_attr, existing):
            _copy_node_to_record(record, node, **node_attr)
    
    def _set_node_type(self, node, node_attr, existing=None):
        
        required = False
        default = None
        node_path = get_node_path(node)
        
        if "required" in node_attr: required = bool(node_attr["required"])
        
        message = f"{node.name} [{node.type}]"
        if required: message += " (required)"
        
        # Set a default if the record already contains the node
        if existing is not None and _record_has_node(existing, node_path):
            existing_node = existing.find_by_path(node_path)
            default = existing_node.value
        
        while True:
            
            try:
                value = inquirer.text(message=message,
                                      render=self._render,
                                      default=default)
            except KeyboardInterrupt:
                sys.exit()
            
            value = _apply_backspace(value)
            
            if value:
                
                # Check if the type is OK (import helpers if needed)
                if "import" in node_attr:
                    import_str = (f'{node_attr["import"]} = '
                              'importlib.import_module(node_attr["import"])')
                    exec(import_str)
                
                val_type = eval(node_attr["type"])
                
                try:
                    val_type(value)
                except:
                    print( "Given value is not compatible with type "
                          f"'{val_type}'" )
                    value = ""
            
            if value or not required: break
        
        if not value: return False
        
        node_attr["value"] = value
        
        return True
    
    def _select_from_list(self, record, node, node_attr, existing=None):
        
        required = False
        default = None
        node_path = get_node_path(node)
        
        # If not yet added, check if node is required
        if (_record_has_node(record, node_path) or
            "required" in node_attr and node_attr["required"] == "True"):
            required = True
        
        # Ask if the node should be added
        if not required:
            
            # Check the default value:
            if existing is not None and _record_has_node(existing, node_path):
                default="yes"
            else:
                default="no"
            
            message = f"Add {node.name}?"
            
            try:
                choice = inquirer.list_input(message,
                                             render=self._render,
                                             choices=['yes', 'no'],
                                             default=default)
            except KeyboardInterrupt:
                sys.exit()
            
            if choice == "no": return
        
        # Add the node to the record if required
        _copy_node_to_record(record, node, **node_attr)
        
        # Gather names of children
        choices = [x.name for x in node.children]
        
        # Check for existing node and then children (i.e. the default value)
        if existing is not None and _record_has_node(existing, node_path):
            existing_node = existing.find_by_path(node_path)
            children = [x.name for x in existing_node.children]
            if children and children[0] in choices: default = children[0]
        
        try:
            choice = inquirer.list_input(node.name,
                                         render=self._render,
                                         choices=choices,
                                         default=default)
        except KeyboardInterrupt:
            sys.exit()
        
        choice_path = f"{node_path}/{choice}"
        chosen_node = self._schema.find_by_path(choice_path)
        chosen_node_attr = get_node_attr(chosen_node, blacklist=["name"])
        
        if "type" in chosen_node_attr:
            self._select_from_type(record,
                                   chosen_node,
                                   chosen_node_attr,
                                   existing)
        
        _copy_node_to_record(record, chosen_node, **chosen_node_attr)
        
        if len(chosen_node.children) < 1: return
            
        if "inquire" in chosen_node_attr:
            new_iter = PreOrderIter(chosen_node, maxlevel=1)
        else:
            new_iter = PreOrderIter(chosen_node, maxlevel=2)
            next(new_iter)
        
        self._iters.append(new_iter)
    
    def _select_from_check(self, record, node, node_attr, existing=None):
        
        required = False
        node_path = get_node_path(node)
        default = None
        
        # Check if required
        if "required" in node_attr and node_attr["required"] == "True":
            required = True
        
        # Prepare message
        if required:
            message = f"{node.name} (select at least one)"
        else:
            message = node.name
        
        # Gather names of children
        choices = [x.name for x in node.children]
        
        # Check for existing node and then children (i.e. the default values)
        if existing is not None and _record_has_node(existing, node_path):
            
            existing_node = existing.find_by_path(node_path)
            children = [x.name for x in existing_node.children]
            
            # Filter children against choices
            if children:
                default = set(choices) & set(children)
                if not default: default = None
        
        while True:
            
            try:
                chosen = inquirer.checkbox(message,
                                           render=self._render,
                                           choices=choices,
                                           default=default)
            except KeyboardInterrupt:
                sys.exit()
            
            if not required or len(chosen) > 0:
                break
        
        if len(chosen) < 1: return
            
        # Add the parent node if it's not already in the tree
        _copy_node_to_record(record, node, **node_attr)
        
        chosen_nodes = []
        
        for choice in chosen:
            
            choise_path = f"{node_path}/{choice}"
            chosen_node = self._schema.find_by_path(choise_path)
            chosen_node_attr = get_node_attr(chosen_node,
                                             blacklist=["name"])
            
            if "type" in chosen_node_attr:
                self._select_from_type(record,
                                       chosen_node,
                                       chosen_node_attr,
                                       existing)
            
            if len(chosen_node.children) > 0:
                chosen_nodes.append(chosen_node)
            
            _copy_node_to_record(record, chosen_node, **chosen_node_attr)
        
        if len(chosen_nodes) < 1: return
        
        new_iter = iter(chosen_nodes)
        self._iters.append(new_iter)


class FlatRecordBuilder(RecordBuilderBase):
    
    def __init__(self, schema, title_sep=":", value_sep=", "):
        super().__init__(schema)
        self._title_sep = title_sep
        self._value_sep = value_sep
    
    def build(self, existing):
        
        self._iters = [iter([self._schema.root_node])]
        record = SCHTree()
        record = self._build(record, existing)
        
        return record
    
    def _build_node(self, record, node, existing):
        
        node_attr = get_node_attr(node, blacklist=["name"])
        
        # See if node requires data first
        if "type" in node_attr:
            
            self._select_from_type(record, node, node_attr, existing)
            
            # If a typed node has no value and no children then we're done
            if "value" not in node_attr or not node.children:
                return
        
        # Now see if the node is a header for list selection
        if "inquire" in node_attr and node_attr["inquire"] == "list":
            self._select_from_list(record, node, node_attr, existing)
            return
        
        # Now see if the node is a header for checkbox selection
        if "inquire" in node_attr and node_attr["inquire"] == "checkbox":
            self._select_from_check(record, node, node_attr, existing)
            return
        
        _copy_node_to_record(record, node, **node_attr)
        
        if len(node.children) < 1: return
        
        new_iter = PreOrderIter(node, maxlevel=2)
        next(new_iter)
        
        self._iters.append(new_iter)
    
    def _select_from_type(self, record, node, node_attr, existing):
        if self._set_node_type(node, node_attr, existing):
            _copy_node_to_record(record, node, **node_attr)
    
    def _set_node_type(self, node, node_attr, existing):
        
        required = False
        node_title = self._get_node_title(node)
        existing_value = existing[node_title]
        
        if "required" in node_attr: required = bool(node_attr["required"])
        
        if required and existing_value is None:
            err_msg = (f"Node {node.name} is required, but existing record"
                        "has no value.")
            raise ValueError(err_msg)
        
        if existing_value is None: return False
        
        if "import" in node_attr:
            import_str = (f'{node_attr["import"]} = '
                      'importlib.import_module(node_attr["import"])')
            exec(import_str)
        
        val_type = eval(node_attr["type"])
        val_type(existing_value)
        node_attr["value"] = existing_value
        
        return True
    
    def _select_from_list(self, record, node, node_attr, existing):
        
        required = False
        node_path = get_node_path(node)
        node_title = self._get_node_title(node)
        existing_value = existing[node_title]
        
        # If not yet added, check if node is required
        if (_record_has_node(record, node_path) or
            "required" in node_attr and node_attr["required"] == "True"):
            required = True
        
        # Gather names of children
        choices = [x.name for x in node.children]
        
        if required and existing_value is None:
            err_msg = (f"Node {node.name} is required, but existing record"
                        "has no value.")
            raise ValueError(err_msg)
        elif required and existing_value not in choices:
            err_msg = f"Entry for required node {node.name} is not valid"
            raise ValueError(err_msg)
        elif (existing_value is None or existing_value not in choices):
            return
        
        # Add the node to the record if required
        _copy_node_to_record(record, node, **node_attr)
        
        choice_path = f"{node_path}/{existing_value}"
        chosen_node = self._schema.find_by_path(choice_path)
        chosen_node_attr = get_node_attr(chosen_node, blacklist=["name"])
        
        if "type" in chosen_node_attr:
            self._select_from_type(record,
                                   chosen_node,
                                   chosen_node_attr,
                                   existing)
        
        _copy_node_to_record(record, chosen_node, **chosen_node_attr)
        
        if len(chosen_node.children) < 1: return
            
        if "inquire" in chosen_node_attr:
            new_iter = PreOrderIter(chosen_node, maxlevel=1)
        else:
            new_iter = PreOrderIter(chosen_node, maxlevel=2)
            next(new_iter)
        
        self._iters.append(new_iter)
    
    def _select_from_check(self, record, node, node_attr, existing):
        
        required = False
        node_path = get_node_path(node)
        node_title = self._get_node_title(node)
        existing_value = existing[node_title]
        
        # Check if required
        if "required" in node_attr and node_attr["required"] == "True":
            required = True
        
        if required and existing_value is None:
            err_msg = (f"Node {node.name} is required, but existing record"
                        "has no value.")
            raise ValueError(err_msg)
        
        if existing_value is None: return
        
        # Check existing values against choices
        choices = [x.name for x in node.children]
        existing_values = set(existing_value.split(self._value_sep))
        valid_values = list(set(choices) & existing_values)
        
        if required and not valid_values:
            err_msg = f"No valid entries found for required node {node.name}"
            raise ValueError(err_msg)
        
        if not valid_values: return
        
        # Sort the values based on the order of choices
        sorter = {k:v for v,k in enumerate(choices)}
        valid_values.sort(key=sorter.get)
        
        # Add the parent node if it's not already in the tree
        _copy_node_to_record(record, node, **node_attr)
        
        chosen_nodes = []
        
        for choice in valid_values:
            
            choise_path = f"{node_path}/{choice}"
            chosen_node = self._schema.find_by_path(choise_path)
            chosen_node_attr = get_node_attr(chosen_node,
                                             blacklist=["name"])
            
            if "type" in chosen_node_attr:
                self._select_from_type(record,
                                       chosen_node,
                                       chosen_node_attr,
                                       existing)
            
            if len(chosen_node.children) > 0:
                chosen_nodes.append(chosen_node)
            
            _copy_node_to_record(record, chosen_node, **chosen_node_attr)
        
        if len(chosen_nodes) < 1: return
        
        new_iter = iter(chosen_nodes)
        self._iters.append(new_iter)
    
    def _get_node_title(self, node):
        
        if node.path == self._schema.root_node.path:
            return node.name
        
        return self._title_sep.join([str(x.name) for x in node.path
                                   if x.path != self._schema.root_node.path])


def _copy_node_to_record(record, node, **node_attr):
    
    parent_path = get_parent_path(node)
    
    if not parent_path:
        record.add_node(node.name, **node_attr)
        return
    
    try:
        node_path = get_node_path(node)
        record.find_by_path(node_path)
    except ChildResolverError:
        record.add_node(node.name, parent_path, **node_attr)


def _record_has_node(record, node_path):
    
    try:
        record.find_by_path(node_path)
        result = True
    except ChildResolverError:
        result = False
    
    return result


def _apply_backspace(s):
    while True:
        # if you find a character followed by a backspace, remove both
        t = re.sub('.\b', '', s, count=1)
        if len(s) == len(t):
            # now remove any backspaces from beginning of string
            return re.sub('\b+', '', t)
        s = t
