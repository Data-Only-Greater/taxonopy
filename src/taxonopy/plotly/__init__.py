
try:
    import plotly
except ImportError:
    msg = "The plotly package must be installed to use this feature"
    raise RuntimeError(msg)
