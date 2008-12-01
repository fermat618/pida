# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

class Enumeration(object):
    """
    Enumeration class for constants
    """
    def __init__(self, name, enumList):
        self.__doc__ = name
        lookup = { }
        i = 0
        for x in enumList:
            if type(x) is tuple:
                x, i = x
            if type(x) is not str:
                raise TypeError, "enum name is not a string: " + x
            if type(i) is not int:
                raise TypeError, "enum value is not an integer: " + i
            if x in lookup:
                raise ValueError, "enum name is not unique: " + x
            if i in lookup:
                raise ValueError, "enum value is not unique for " + x
            lookup[x] = i
            lookup[i] = x
            i = i + 1
        self.lookup = lookup

        self._fixed = True

    def __getattr__(self, attr):
        try:
            return self.lookup[attr]
        except KeyError:
            raise AttributeError, attr

    def __setattr__(self, key, value):
        if not hasattr(self, '_fixed'):
            object.__setattr__(self, key, value)
        else:
            raise ValueError, "Can't change a Enumeration object"

    def whatis(self, value):
        return self.lookup[value]

    def __repr__(self):
        return '<Enumeration %s>' %self.__doc__
