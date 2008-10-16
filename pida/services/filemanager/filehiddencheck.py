# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

SCOPE_PROJECT  = 0
SCOPE_GLOBAL = 1

def fhc(scope, label):
    def decorate(fn):
        fn.scope = scope
        fn.label = label
        fn.identifier = fn.__name__
        return fn
    return decorate

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
