"""
    pida.utils.descriptors
    ~~~~~~~~~~~~~~~~~~~~~~

    some utility descriptor classes

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

class cached_property(object):
    """
    descriptor implementing "cached property", i.e. the function
    calculating the property value is called only once

    >>> class Test(object):
    ...     @cached_property
    ...     def attr(self):
    ...         print 'did it'
    ...         return 2
    >>> Test.attr
    <cached_property: attr>
    >>> test = Test()
    >>> test.attr
    did it
    2
    >>> test.attr
    2

    """

    def __init__(self, func, name=None, doc=None):
        assert callable(func)
        self.func = func
        self.__name__ = name or func.__name__
        self.__doc__ = doc or func.__doc__
    
    def __get__(self, obj, type_=None):
        if obj is None:
            return self

        value = self.func(obj)
        setattr(obj, self.__name__, value)

        return value

    def __repr__(self):
        return '<cached_property: %s>'%self.__name__
