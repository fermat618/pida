# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import types, exceptions

class EnumException(exceptions.Exception):
    pass

class Enumeration(object):
    """
    Enumeration class for constants
    """
    def __init__(self, name, enumList, valuesAreUnique=True):
        self.__doc__ = name
        lookup = { }
        reverseLookup = { }
        i = 0
        uniqueNames = {}
        uniqueValues = {}
        for x in enumList:
            if type(x) == types.TupleType:
                x, i = x
            if type(x) != types.StringType:
                raise EnumException, "enum name is not a string: " + x
            if type(i) != types.IntType:
                raise EnumException, "enum value is not an integer: " + i
            if uniqueNames.has_key(x):
                raise EnumException, "enum name is not unique: " + x
            if valuesAreUnique and uniqueValues.has_key(i):
                raise EnumException, "enum value is not unique for " + x
            uniqueNames[x] = 1
            uniqueValues[i] = 1
            lookup[x] = i
            reverseLookup[i] = x
            i = i + 1
        self.lookup = lookup
        self.reverseLookup = reverseLookup

        self._fixed = True

    def __getattr__(self, attr):
        try: return self.lookup[attr]
        except KeyError: raise AttributeError

    def __setattr__(self, key, value):
        if not hasattr(self, '_fixed'):
            super(Enumeration, self).__setattr__(key, value)
        else:
            raise ValueError, "Can't change a Enumeration object"

    def whatis(self, value):
        return self.reverseLookup[value]

    def __repr__(self):
        return '<Enumeration %s>' %self.__doc__
