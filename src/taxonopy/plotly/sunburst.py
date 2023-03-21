
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go

from taxonopy.schema import get_node_path


class Sunburst():
    
    def __init__(self, schema, db):
        self._schema = schema
        self._db = db
    
    def from_paths(self, *paths):
        
        proj = self._db.projection(paths)
        data = defaultdict(list)
        
        for i in range(len(paths)):

            proj_slice = [proj[path] for path in paths[:i+1]]

            for x in zip(*proj_slice):

                if not all(x): continue

                name = " & ".join(x[-1]['children'])
                parent = x[0]['name']

                if len(x) > 1:
                    for j in range(len(x) - 1):
                        parent += ": " + " & ".join(x[j]['children'])

                data["name"].append(name)
                data["parent"].append(parent)
                data["id"].append(f'{parent}: {name}')

        df = pd.DataFrame(data)
        counts_series = df.value_counts()
        counts_df = counts_series.reset_index(name="count")

        name_parts = [path.split("/")[-1] for path in paths]
        row_data = {"name": ["DB"],
                    "parent": [None],
                    "id": [name_parts[0]],
                    "count": [len(proj['id'])]}
        final_df = pd.concat([counts_df, pd.DataFrame(row_data)],
                             ignore_index=True)

        fig = go.Figure(go.Sunburst(ids=final_df['id'],
                                    labels=final_df['name'],
                                    parents=final_df['parent'],
                                    values=final_df['count'],
                                    branchvalues="total"))

        return fig
    
    def from_children(self, root_path):
        
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
        
        return self.from_paths(*paths)
