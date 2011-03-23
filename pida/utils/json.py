"""
    a wrapper around json that adds some simple perks around stdlib json load/dump
    in particular py.path support and default indent
"""

from __future__ import absolute_import
import json
import py

def dump(data, path, indent=2, sort_keys=True, **kw):
    with path.open('w') as fp:
        json.dump(data, fp, indent=indent, sort_keys=sort_keys, **kw)

def load(path, fallback=None):
    try:
        with path.open() as fp:
            return json.load(fp)
    except:
        #XXX log?
        if fallback is not None:
            return fallback
        raise
