
from collections import defaultdict
from itertools import chain, product

import plotly.graph_objects as go

from ..db import make_query


class Sankey():
    
    def __init__(self, schema, db):
        self._schema = schema
        self._db = db

    def __call__(self, apath, bpath, cpath=None):
        
        aranks, anames = self.get_ranks_names(apath, 0)
        branks, bnames = self.get_ranks_names(bpath, 1)
        all_ranks = [aranks, branks]
        all_names = [anames, bnames]
    
        prodab = list(product(anames, bnames))
        
        if cpath is not None:
            cranks, cnames = self.get_ranks_names(cpath, 2)
            all_ranks.append(cranks)
            all_names.append(cnames)
            #prodbc = list(product(bnames, cnames))
        
        ranks = dict(chain.from_iterable(d.items() for d in all_ranks))
        names = dict(chain.from_iterable(d.items() for d in all_names))
        names_lookup = self.lookup_names(names)
        
        source, target, value, matches = get_links(prodab, names_lookup)
        
        if cpath is not None:
            csource, ctarget, cvalue = get_links_conservative(bnames,
                                                              cnames,
                                                              names_lookup,
                                                              matches)
            source.extend(csource)
            target.extend(ctarget)
            value.extend(cvalue)
        
        source, target, label, label_keys = get_labels(source, target, names)
        x, y = get_positions(ranks, label_keys)
        column_x, column_text = get_columns(apath, bpath, cpath)
        
        fig = go.Figure(data=[go.Sankey(
            arrangement='snap',
            node = dict(
              pad = 15,
              thickness = 20,
              line = dict(width = 0.5),
              label = label,
              x = x,
              y = y
            ),
            link = dict(
              source = source,
              target = target,
              value = value
            ),
            selectedpoints=[1])])
    
        for x, text in zip(column_x, column_text):
          fig.add_annotation(
                  x=x,
                  y=1.1,
                  text=text,
                  showarrow=False,
                  font=dict(
                      family="Courier New, monospace",
                      size=16,
                      ),
                  align="center")
        
        return fig
    
    def get_ranks_names(self, path, rank):
        
        ranks = {}
        names = {}
        
        node = self._schema.find_by_path(path)
        ranks = {f"{path}/{child.name}": rank for child in node.children}
        names = {f"{path}/{child.name}": f"{child.name}" 
                                                 for child in node.children}
        
        return ranks, names
    
    def lookup_names(self, names):
        
        names_lookup = {}
    
        for k in names.keys():
            query = make_query(k)
            memdb = self._db.search(query)
            names_lookup[k] = memdb.to_records().keys()
            
        return names_lookup


def get_links(prod, names_lookup):

    source = []
    target = []
    value = []
    matches = defaultdict(list)

    for s, t in prod:

        a = names_lookup[s]
        b = names_lookup[t]
        
        match = list(set(a) & set(b))
        count = len(match)
        matches[t].extend(match)

        if count == 0: continue

        source.append(s)
        target.append(t)
        value.append(count)
    
    return source, target, value, matches


def get_links_explicit(prod, names_lookup, matches):

    source = []
    target = []
    value = []

    for s, t in prod:

        a = matches[s]
        b = names_lookup[t]

        match = [1 if x in b else 0 for x in a]
        count = sum(match)

        if count == 0: continue

        source.append(s)
        target.append(t)
        value.append(count)
    
    return source, target, value


def get_links_conservative(bnames, cnames, names_lookup, matches):

    source = []
    target = []
    value = []

    for s in bnames:

        if s not in matches: continue

        total_hits = [0] * len(cnames)

        for pid in matches[s]:

            hit = []

            for t in cnames:

                b = names_lookup[t]

                if pid in b:
                    hit.append(1)
                else:
                    hit.append(0)

            hit = [x / sum(hit) if sum(hit) > 0 else 0 for x in hit]
            total_hits = [x + y for x, y in zip(hit, total_hits)]

        for t, v in zip(cnames, total_hits):

            if v == 0: continue

            source.append(s)
            target.append(t)
            value.append(v)

    return source, target, value


def get_labels(source, target, names):
    
    unique = lambda x: list(dict.fromkeys(x))

    label_keys = unique(source + target)
    source = [label_keys.index(s) for s in source]
    target = [label_keys.index(t) for t in target]
    label = [names[l] for l in label_keys]
    
    return source, target, label, label_keys


def get_positions(ranks, label_keys):

    base = 0.1
    xstep = 0.8 / max(ranks.values())

    x = [base + ranks[l] * xstep for l in label_keys]
    y = [0.1] * len(x)
    
    return x, y


def get_columns(apath, bpath, cpath=None):
    
    get_name = lambda path: path.split("/")[-1]
    
    text = [get_name(apath), get_name(bpath)]
    if cpath is not None:
        text.append(get_name(cpath))
    
    base = 0.1
    xstep = 0.8 / (len(text) - 1)
    
    x = [base + xstep * i for i, _ in enumerate(text)]
    
    return x, text
