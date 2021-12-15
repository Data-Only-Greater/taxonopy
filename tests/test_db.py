
from collections import OrderedDict

from taxonopy.db import _order_data


def test_order_data():
    
    test = {"_default": {"2": {"b": [{"name": "b",
                                      "y": 2,
                                      "x": 1},
                                     {"name": "a",
                                      "d": 4,
                                      "c": 3}],
                               "a": [{"name": "x",
                                      "parent": "a",
                                      "f": 6,
                                      "e": 5},
                                     {"name": "y",
                                      "parent": "a",
                                      "h": 8,
                                      "g": 7},
                                     {"name": "x",
                                      "parent": "b",
                                      "f": 6,
                                      "e": 5},
                                     {"name": "y",
                                      "h": 8,
                                      "g": 7}]},
                         "1": {"b": [{"name": "b",
                                      "y": 2,
                                      "x": 1},
                                     {"name": "a",
                                      "d": 4,
                                      "c": 3}],
                               "a": [{"name": "y",
                                      "f": 6,
                                      "e": 5},
                                     {"name": "x",
                                      "h": 8,
                                      "g": 7}]}}}
    
    expected = {
        '_default': {'1': {'a': [{'g': 7, 'h': 8, 'name': 'x'},
                                 {'e': 5, 'f': 6, 'name': 'y'}],
                           'b': [{'c': 3, 'd': 4, 'name': 'a'},
                                 {'name': 'b', 'x': 1, 'y': 2}]},
                     '2': {'a': [{'e': 5, 'f': 6, 'name': 'x', 'parent': 'a'},
                                 {'g': 7, 'h': 8, 'name': 'y', 'parent': 'a'},
                                 {'e': 5, 'f': 6, 'name': 'x', 'parent': 'b'},
                                 {'g': 7, 'h': 8, 'name': 'y'}],
                           'b': [{'c': 3, 'd': 4, 'name': 'a'},
                                 {'name': 'b', 'x': 1, 'y': 2}]}}
        }
    
    ordered = _order_data(test)
    
    assert OrderedDict(ordered) == OrderedDict(expected)
