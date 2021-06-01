# -*- coding: utf-8 -*-

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata


def get_name():
    return __name__


def get_version():
    return metadata.version(get_name())
