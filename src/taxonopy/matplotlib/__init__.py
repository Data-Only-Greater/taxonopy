
try:
    import matplotlib
except ImportError:
    msg = "The matplotlib package must be installed to use this feature"
    raise RuntimeError(msg)

from .bar import _bar as bar

__all__ = ["bar"]
