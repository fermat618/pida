
__all__ = ['dumps', 'loads', 'dump', 'load']
try:
    from json import loads, dumps, load, dump
    #XXX: silence the broken pyflakes
    loads, dumps, load, dump
except ImportError:
    from simplejson import loads, dumps, load, dump
