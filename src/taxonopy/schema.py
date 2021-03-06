
import os
import json
import datetime as dt
import textwrap
from abc import ABC, abstractmethod
from copy import deepcopy
from collections import OrderedDict

from anytree import (ContStyle,
                     LevelOrderGroupIter,
                     Node,
                     PreOrderIter,
                     RenderTree)
from anytree.exporter import UniqueDotExporter
from anytree.resolver import ChildResolverError, Resolver
from anytree.search import findall
from tabulate import tabulate

# TODO make the color scheme dynamic
COLOR_SCHEME = ["aliceblue", "antiquewhite", "azure", "coral", "palegreen"]


class Tree:
    
    def __init__(self, root_node=None,
                       short_attrs=None,
                       long_attrs=None,
                       level_prefix="L"):
        self.root_node = root_node
        self.short_attrs = (set([]) if short_attrs is None
                                                        else set(short_attrs))
        self.long_attrs = (set([]) if long_attrs is None else set(long_attrs))
        self.prefix = level_prefix
    
    @classmethod
    def from_dict(cls, data, level_prefix="L"):
        
        data = deepcopy(data)
        
        n_levels = len(list(data.keys()))
        new_tree = cls(level_prefix)
        
        # read the root node
        root = data[f"{new_tree.prefix}0"][0]
        assert "name" in root
        name = root.pop("name")
        new_tree.add_node(name, **root)
        
        # populate the tree
        for k in range(1, n_levels):
            
            key = f"{new_tree.prefix}{k}"
            nodes = data[key]
            
            for n in nodes:
                
                assert "name" in n
                assert "parent" in n
                name = n.pop("name")
                parent = n.pop("parent")
                new_tree.add_node(name, parent, **n)
        
        return new_tree
    
    @classmethod
    def from_json(cls, filepath_or_data, level_prefix="L"):
        """
        Read the taxonomy from a JSON string or file path given as input
        The JSON file needs to have the following format:
        
        {
            "L0": [
                {
                    "name": "level0",
                }
            ],
            "L1": [
                {
                    "name": "level1",
                    "parent": "level0",
                }
            ]
        }
        
        Parameters
        ----------
        file_name: str with the name of the file containing the taxonomy
        """
        
        data = json.loads(_get_data(filepath_or_data))
        new_tree = cls.from_dict(data, level_prefix)
        
        return new_tree
    
    def to_dict(self):
        
        if self.root_node is None: return {}
        
        output_dict = OrderedDict()
        
        for i, children in enumerate(LevelOrderGroupIter(self.root_node)):
            
            node_list = []
            
            for node in children:
                
                # Must have name and parent
                node_dict = OrderedDict([("name", node.name)])
                
                if node.parent is not None:
                    
                    node_path = get_node_path(node)
                    node_resolution = node_path.strip('/').split('/')
                    parent_path = '/'.join(node_resolution[:-1])
                    
                    node_dict["parent"] = parent_path
                
                for attr in sorted(self.short_attrs.union(self.long_attrs)):
                    if hasattr(node, attr):
                        node_dict[attr] = getattr(node, attr)
                
                node_list.append(node_dict)
            
            output_dict[f"L{i}"] = node_list
        
        return output_dict
    
    def to_dot(self, file_name=None, root_path=None, nodeattr_fn=None):
        
        def basic_nodeattr_fn(node):
            return (f'label="{node.name}" '
                     'style=filled '
                    f'color={COLOR_SCHEME[node.depth]}')
        
        if nodeattr_fn is None: nodeattr_fn = basic_nodeattr_fn
        
        if root_path is None:
            root = self.root_node
        else:
            root = self.find_by_path(root_path)
            
        dot = UniqueDotExporter(
            root,
            nodeattrfunc=nodeattr_fn,
            options=[
                'graph [layout = dot, ranksep="1.5", nodesep="0.7"]',
                'rankdir ="LR"',
                'node [fontname="Arial"]'
            ]
        )
        
        dot_text = "\n".join([l for l in dot])
        
        if file_name is None:
            return dot_text
        
        with open(file_name, "w") as f:
            f.write(dot_text)
        
        return 
    
    def to_json(self, file_name=None):
        
        output_dict = self.to_dict()
        json_text = json.dumps(output_dict, indent=4)
        
        if file_name is None:
            return json_text
        
        with open(file_name, "w") as f:
            f.write(json_text)
    
    def to_tree(self, path=None):
        
        extra_attrs = self.short_attrs.union(self.long_attrs)
        
        # Copy the entire tree
        if path is None:
            new_root = copy_node(self.root_node, extra_attrs)
            return type(self)(new_root, self.short_attrs, self.long_attrs)
        
        node = self.find_by_path(path)
        new_root = copy_node(self.root_node, extra_attrs, orphan=True)
        last_node = new_root
        
        for top_node in node.ancestors[1:]:
            next_node = copy_node(top_node, extra_attrs, orphan=True)
            last_node.children = [next_node]
            last_node = next_node
        
        final_node = copy_node(node, extra_attrs)
        last_node.children = [final_node]
    
        return type(self)(new_root, self.short_attrs, self.long_attrs)
    
    def find_by_name(self, name, parent_path=None):
        
        if parent_path is None:
            root = self.root_node
        else:
            root = self.find_by_path(parent_path)
        
        nodes = findall(root, lambda node: node.name == name)
        
        if len(nodes) == 1:
            return nodes[0]
        
        return nodes
    
    def find_by_path(self, path) -> Node:
        
        r = Resolver()
        path_resolution = path.strip('/').split('/')
        
        if (len(path_resolution) == 1 and
            self.root_node.name == path_resolution[0]):
            return self.root_node
        elif len(path_resolution) == 1:
            raise ChildResolverError(self.root_node, path, 'name')
        
        path_relative = '/'.join(path_resolution[1:])
        
        return r.get(self.root_node, path_relative)
    
    def add_node(self, name, parent=None, children=None, **kwargs):
        
        if "long_attrs" in kwargs:
            self.long_attrs |= set(kwargs["long_attrs"])
        
        self.short_attrs |= set(kwargs.keys()) - self.long_attrs
        
        if parent is None:
            self.root_node = Node(name, children=children, **kwargs)
            return
        
        parent_node = self.find_by_path(parent)
        Node(name, parent=parent_node, children=children, **kwargs)
    
    def delete_node(self, path):
        node = self.find_by_path(path)
        node.parent = None
    
    def update_node(self, path, **kwargs):
        
        node = self.find_by_path(path)
        
        for attr, value in kwargs.items():
            setattr(node, attr, value)
    
    def diff(self, other):
        
        # Can only be compared with another Tree
        if not isinstance(other, Tree):
            raise ValueError("Comparison only valid to another Tree object")
        
        diff = {}
        
        deleted = "deleted"
        added = "added"
        changed = "changed"
        
        # Check for added and deleted nodes
        flat_nodes = [node for node in PreOrderIter(self.root_node)]
        node_paths = [get_node_path(node) for node in flat_nodes]
        other_node_paths = [get_node_path(node)
                                    for node in PreOrderIter(other.root_node)]
        
        for path in (set(node_paths) - set(other_node_paths)):
            diff[path] = deleted
        
        for path in (set(other_node_paths) - set(node_paths)):
            diff[path] = added
        
        # Check for changed nodes
        for path in (set(node_paths) & set(other_node_paths)):
            
            this_node = self.find_by_path(path)
            other_node = other.find_by_path(path)
            
            matching = True
            
            for attr in self.short_attrs.union(self.long_attrs):
                
                if ((hasattr(this_node, attr) and
                     not hasattr(other_node, attr)) or
                    (not hasattr(this_node, attr) and
                     hasattr(other_node, attr))):
                    
                    matching = False
                    break
                
                elif (not hasattr(this_node, attr) or
                      not hasattr(other_node, attr)):
                    
                    continue
                
                this_attr = getattr(this_node, attr)
                other_attr = getattr(other_node, attr)
                
                if this_attr == other_attr: continue
                matching = False
                break
            
            if matching: continue
            diff[path] = changed
        
        return diff
    
    def __eq__(self, other):
        if not isinstance(other, Tree): return False
        return not self.diff(other)
    
    def __str__(self):
        return render_node(self.root_node,
                           short_attrs=self.short_attrs,
                           long_attrs=self.long_attrs)


class SCHTree(Tree):
    
    def add_node(self, name, parent=None, **kwargs):
        
        data = {}
        extra_keys = ["type",
                      "default",
                      "value",
                      "inquire",
                      "required",
                      "import",
                      "children",
                      "long_attrs",
                      "description"]
        
        for key in extra_keys:
            if key in kwargs: data[key] = kwargs[key]
        
        super().add_node(name, parent, **data)
    
    def to_dot(self, file_name=None, root_path=None):
        
        def SCH_nodeattr_fn(node):
            
            if hasattr(node, "type"):
                nodeattr = (f'label=<{node.name}'
                             '<BR /><FONT POINT-SIZE="10">'
                             f'{getattr(node, "type")}'
                             '</FONT>> ')
            else:
                nodeattr = f'label="{node.name}" '
            
            nodeattr += ( 'style=filled '
                         f'color={COLOR_SCHEME[node.depth]}')
            
            return nodeattr
        
        return super().to_dot(file_name=file_name,
                              root_path=root_path,
                              nodeattr_fn=SCH_nodeattr_fn)
    
    def to_pandoc(self, title="Schema Glossary",
                        width=120,
                        date_format="%d %B %Y",
                        file_name=None):
        
        nodes = [self.root_node]
        msgs = document(nodes,
                        title,
                        date_format=date_format,
                        attrs=["description"],
                        attrs_names=["Description"],
                        width_attr="description",
                        width=width)
        
        if file_name is None:
            return msgs
        
        with open(file_name, "wt") as f:
            for msg in msgs:
                f.write(msg + "\n")


class RecordBuilderBase(ABC):
    
    def __init__(self, schema):
        
        self._schema = schema
        self._iters = None
    
    @abstractmethod
    def build(self, existing=None, **kwargs):
        return
    
    def _build(self, record, existing=None, **kwargs):
        
        while True:
            try:
                self._next(record, existing, **kwargs)
            except StopIteration:
                break
        
        self._iters = None
        
        return record
    
    def _next(self, record, existing=None, **kwargs):
        
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
        
        self._build_node(record, node, existing, **kwargs)
    
    @abstractmethod
    def _build_node(record, node, existing=None, **kwargs):
        return


def get_node_path(node):
    return node.separator.join([""] + [str(x.name) for x in node.path])


def copy_node(node, extra_attrs, orphan=False):
    
    children = None
    kwargs = {attr: getattr(node, attr)
                          for attr in extra_attrs if hasattr(node, attr)}
    if not orphan: children = deepcopy(node.children)
    
    return Node(node.name, children=children, **kwargs)


def render_node(root, short_attrs=None, long_attrs=None):
    
    if short_attrs is None: short_attrs = []
    if long_attrs is None: long_attrs = []
    
    msg = ''
    
    for pre, fill, node in RenderTree(root):
        
        msg += f"{pre}{node.name}"
        
        for attr in short_attrs:
            if hasattr(node, attr):
                msg += f" {attr}={getattr(node, attr)}"
        
        msg += "\n"
        
        for attr in long_attrs:
            if hasattr(node, attr):
                msg += render_lines(fill, node, attr)
    
    return msg


def render_lines(fill, node, attr, pad=2, wrap=79, style=None):
    
    if style is None: style = ContStyle()
    vertical = style.vertical[0]
    
    attr_key = f"{attr}: "
    attr_value = f"{getattr(node, attr)}"
    padding = " " * (pad - 1)
    
    if node.children:
        if len(fill) == 1:
            fill = vertical
        else:
            padding = f"{vertical}{padding}"
    else:
        padding += " "
    
    true_wrap = wrap - pad - len(fill) - len(attr_key)
    wrapped = textwrap.wrap(attr_value, true_wrap)
    
    if not wrapped: return ""
    
    msg = f"{fill}{padding}{attr_key}{wrapped[0]}\n"
    attr_pad = " " * len(attr_key)
    
    for line in wrapped[1:]:
        msg += f"{fill}{padding}{attr_pad}{line}\n"
    
    return msg


def get_parent_path(node):
    return node.separator.join([""] + [str(x.name) for x in node.path[:-1]])


def get_node_attr(node, blacklist=None):
    
    if blacklist is None: blacklist = []
    
    return {key: value for key, value in filter(
                lambda item: not item[0].startswith("_") and
                             item[0] not in blacklist,
                    sorted(node.__dict__.items(), key=lambda item: item[0]))}


def record_has_node(record, node_path):
    
    try:
        record.find_by_path(node_path)
        result = True
    except ChildResolverError:
        result = False
    
    return result


def copy_node_to_record(record, node, **node_attr):
    
    parent_path = get_parent_path(node)
    
    if not parent_path:
        record.add_node(node.name, **node_attr)
        return
    
    try:
        node_path = get_node_path(node)
        record.find_by_path(node_path)
    except ChildResolverError:
        record.add_node(node.name, parent_path, **node_attr)


def document(nodes,
             title,
             date_format="%d %B %Y",
             attrs=None,
             attrs_names=None,
             width_attr=None,
             width=None,
             _msgs=None,
             _parent=None,
             _attrs_width=None):
    
    get_dot_path = \
        lambda x: ".".join([n.name.lower() for n in x.path]).replace(" ", "_")
    
    if attrs is None: attrs = []
    if attrs_names is None: attrs_names = []
    
    if _msgs is None:
        date = dt.date.today()
        msgs = [f"% {title}",
                "%",
                f"% {date.strftime(date_format)}",
                ""]
    else:
        msgs = _msgs
    
    if _parent is None:
        caption = "Root node"
        dot_path = "root"
    else:
        caption = f'Children of "{_parent.name}"'
        dot_path = get_dot_path(_parent)
    
    if _attrs_width is None: _attrs_width = 999    
    
    headers = ["Name"] + attrs_names + ["Children"]
    table = []
    
    for node in nodes:
        
        name = node.name
        attrs_values = [None] * len(attrs_names)
        children = None
        
        for i, attr in enumerate(attrs):
            if hasattr(node, attr):
                value = getattr(node, attr)
                if attr == width_attr:
                    value = textwrap.fill(value, _attrs_width)
                attrs_values[i] = value
        
        if node.children:
            children = f"[@tbl:{get_dot_path(node)}]"
        
        table.append([name] + attrs_values + [children])
    
    msgs += tabulate(table, headers, tablefmt="grid").split("\n")
    msgs.append("")
    msgs.append(f": {caption} {{#tbl:{dot_path}}}")
    msgs.append("")
    
    for node in nodes:
        if not node.children: continue
        document(node.children,
                 title,
                 attrs=attrs,
                 attrs_names=attrs_names,
                 width_attr=width_attr,
                 _msgs=msgs,
                 _parent=node,
                 _attrs_width=_attrs_width)
    
    # Check the width if this is root
    if _parent is None and width is not None:
        max_width = max([len(msg) for msg in msgs])
        if max_width > width:
            _attrs_width -= (max_width - width)
            msgs = document(nodes,
                            title,
                            date_format=date_format,
                            attrs=attrs,
                            attrs_names=attrs_names,
                            width_attr=width_attr,
                            width=width,
                            _msgs=None,
                            _parent=None,
                            _attrs_width=_attrs_width)
    
    return msgs


def _get_data(filepath_or_data):
    
    if _file_exists(filepath_or_data):
        with open(filepath_or_data, "r") as f:
            filepath_or_data = f.read()
    
    return filepath_or_data


def _file_exists(filepath_or_data):
    
    exists = False
    
    try:
        exists = os.path.exists(filepath_or_data)
    except (TypeError, ValueError):
        pass
    
    return exists
