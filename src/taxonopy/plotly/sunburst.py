
from collections import defaultdict
from itertools import islice, cycle

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from taxonopy.schema import get_node_path


class Sunburst():
    
    def __init__(self, schema, db):
        self._schema = schema
        self._db = db
    
    def from_paths(self, *paths, include_root=False):
        
        [self._schema.find_by_path(path) for path in paths]
        proj = self._db.projection(paths)
        data = defaultdict(list)
        
        for i in range(len(paths)):
            
            proj_slice = [proj[path] for path in paths[:i+1]]
            
            for x in zip(*proj_slice):
                
                if not all(x): continue
                
                name = " & ".join(x[-1]['children'])
                
                if include_root:
                    parent = x[0]['name']
                else:
                    parent = "DB"
                
                if len(x) > 1:
                    for j in range(len(x) - 1):
                        parent += ": " + " & ".join(x[j]['children'])
                
                data["name"].append(name)
                data["parent"].append(parent)
                data["id"].append(f'{parent}: {name}')
        
        df = pd.DataFrame(data)
        counts_series = df.value_counts()
        counts_df = counts_series.reset_index(name="count")
        
        if include_root:
            root_name = paths[0].split("/")[-1]
            counts_df = counts_df.sort_values(
                by=["parent"],
                key=lambda x: x.map({root_name: 0}).fillna(1))
        
        data = defaultdict(list)
    
        data["name"].append("DB"),
        data["parent"].append(None),
        data["id"].append("DB"),
        data["count"].append(len(proj['id']))
        
        if include_root:
            data["name"].append(root_name),
            data["parent"].append("DB"),
            data["id"].append(root_name),
            data["count"].append(len([1 for x in proj[paths[0]] if x]))
        
        final_df = pd.concat([pd.DataFrame(data), counts_df],
                             ignore_index=True)
        
        marker = None
        
        if include_root:
            counts_df_tip = counts_df[counts_df["parent"] == root_name]
            segment_colors = list(islice(cycle(px.colors.qualitative.Plotly),
                                         len(counts_df_tip))) 
            color_discrete_sequence = ["", "#7c7c7c"] + segment_colors
            marker = dict(colors=color_discrete_sequence)
        
        fig = go.Figure(go.Sunburst(ids=final_df['id'],
                                    labels=final_df['name'],
                                    parents=final_df['parent'],
                                    values=final_df['count'],
                                    branchvalues="total",
                                    marker=marker))
        
        return fig
    
    def from_children(self, root_path, include_root=True):
        
        def _get_paths(node, paths=None):
    
            if paths is None:
                paths = [get_node_path(node)]
            else:
                paths.append(get_node_path(node))

            dependants = []

            for child in node.children:
                if child.children:
                    dependants.append(child)

            if len(dependants) == 0:
                return paths
            elif len(dependants) > 1:
                raise RuntimeError('Multiple dependants detected')

            return _get_paths(dependants[0], paths)
        
        root_node = self._schema.find_by_path(root_path)
        paths = _get_paths(root_node)
        
        return self.from_paths(*paths, include_root=include_root)
