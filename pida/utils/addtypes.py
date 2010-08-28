# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import bisect

class Enumeration(object):
    """
    Enumeration class for constants
    """
    __slots__ = '_name', '_lookup'

    def __init__(self, name, enumlist):
        self._name = name
        lookup = {}
        i = 0
        for x in enumlist:
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
        self._lookup = lookup

    def __getattr__(self, attr):
        try:
            return self._lookup[attr]
        except KeyError:
            raise AttributeError, attr

    def whatis(self, value):
        """
        Return the name that represents this value
        """
        return self._lookup[value]

    def __repr__(self):
        return '<Enumeration %s>' %self._name

class PriorityList(list):
    """
    The lazy priorty list is a special that allows the entries
    to be sorted by a previous supplied list or a function.
    The list itself holds itself sorted
    """
    
    def __init__(self, *args, **kwargs):
        self._sort_list = None
        list.__init__(self, args)
        self._keyfnc = kwargs.pop('key', None)
        self.set_sort_list(list(kwargs.pop('sort_list', ())))
        self.sort()
        
    def set_sort_list(self, lst):
        """
        Set the list of attributes to return
        """
        self._sort_list = lst
        self.sort()

    def get_sort_list(self):
        """
        Return the list after which this PriorityList should be sorted
        """
        return self._sort_list

    @property
    def _keyfnc_default(self):
        return self._keyfnc

    def _sort_iterator(self):
        for x in self._sort_list:
            yield x

    def sort(self, reverse=False):
        """
        Sort the PriorityList
        """
        if self._sort_list:
            tmp = self[:]
            del self[:]
            cache = {}
            if self._keyfnc:
                for i in tmp:
                    cache[self._keyfnc(i)] = i
            else:
                for i in tmp:
                    cache[i] = i
            j = 0
            for i in self._sort_iterator():
                if i in cache:
                    addo = cache[i]
                    self.insert(j+1, addo)
                    try:
                        tmp.remove(addo)
                    except ValueError:
                        pass
                    j += 1
            # we put the rest of the keys that are not in 
            # the sort_list into self, but sort them internaly
            tmp.sort(key=self._keyfnc_default, reverse=reverse)
            self.extend(tmp)

        else:
            list.sort(self, key=self._keyfnc, reverse=reverse)


    def add(self, item):
        """
        Adds a item to the list.This will use the supplied order from the 
        sort_list
        """
        # we can't use biselect, because it's a customized list
        # and key access
        #if not self._sort_list:
        #    bisect.insort_right(self, item)
        #else:
        self.append(item)
        self.sort()

    def replace(self, items):
        del self[:]
        for x in items:
            self.append(x)
