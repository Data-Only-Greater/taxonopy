
import os
import json

from anytree import LevelOrderGroupIter, Node, RenderTree
from anytree.exporter import UniqueDotExporter
from anytree.search import find

# TODO make the color scheme dynamic
COLOR_SCHEME = ["aliceblue", "antiquewhite", "azure", "coral", "palegreen"]


class TaxonomyParser:
    
    """
    This class is a wrapper on a Tree class from the anytree library to hold
    different taxonomies read from a JSON representation
    
    Attributes
    ----------
    prefix: str with the prefix character for each level in the JSON
            representation
    nodes: dict with node name str as key and anytree Node instance as value
           which contains all the nodes of the taxonomy tree
    root_key: str identifying the root node for fast retrieval
    """
    
    def __init__(self, level_prefix = "L"):
        self.prefix = level_prefix
        self.nodes = {}
        self.root_key = None
        self.extra_attrs = set([])
    
    def find_by_name(self, name) -> Node:
        """
        Retrieve a node by its name
        
        Parameters
        ----------
        name: str holding the name to be looked for
        
        Returns
        -------
        node: an anytree Node instance with the seeked node
        """
        root = self.nodes[self.root_key]
        node = find(root, lambda node: node.name == name)
        return node
    
    def from_json(self, filepath_or_data):
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
        n_levels = len(list(data.keys()))
        
        # read the root node
        root = data[f"{self.prefix}0"][0]
        name = root.pop("name")
        
        self.nodes = {}
        self.extra_attrs |= set(root.keys())
        
        self.nodes[name] = Node(name, **root)
        self.root_key = name
        
        # populate the tree
        for k in range(1, n_levels):
            
            key = f"{self.prefix}{k}"
            nodes = data[key]
            
            for n in nodes:
                
                assert "name" in n
                assert "parent" in n
                name = n.pop("name")
                parent = n.pop("parent")
                
                self.extra_attrs |= set(n.keys())
                
                self.nodes[name] = Node(
                    name,
                    parent=self.nodes[parent],
                    **n
                )
    
    def to_dot(self, file_name=None):
        
        def nodeattr_fn(node):
            return (f'label="{node.name}" '
                     'style=filled '
                    f'color={COLOR_SCHEME[node.depth]}')
        
        root = self.nodes[self.root_key]
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
        
        output_dict = {}
        
        for i, children in enumerate(LevelOrderGroupIter(
                                                self.nodes[self.root_key])):
            
            node_list = []
            
            for node in children:
                
                # Must have name and parent
                node_dict = {"name": node.name}
                if node.parent is not None:
                    node_dict["parent"]= node.parent.name
                
                for attr in self.extra_attrs:
                    if hasattr(node, attr):
                        node_dict[attr] = getattr(node, attr)
                
                node_list.append(node_dict)
            
            output_dict[f"L{i}"] = node_list
        
        json_text = json.dumps(output_dict, indent=4)
        
        if file_name is None:
            return json_text
        
        with open(file_name, "w") as f:
            f.write(json_text)
    
    def __str__(self):
        """
        ASCII representation of the tree similarly to a directory structure
        
        Returns
        -------
        msg: a str containing the output taxonomy visualization
        """
        msg = """"""
        root = self.nodes[self.root_key]
        for pre, _, node in RenderTree(root):
            
            msg += f"{pre}{node.name}"
            
            for attr in self.extra_attrs:
                if hasattr(node, attr):
                    msg += f" {attr}={getattr(node, attr)}"
            
            msg += "\n"
            
        return msg


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
