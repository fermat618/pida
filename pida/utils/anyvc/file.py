# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    anyvcs file helpers
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2006 by Ronny Pfannschmidt

    :license: BSD License
"""

from os.path import dirname, basename, join

class StatedPath(object):
    """
    stores status informations about files

    >>> StatedPath("a.txt", "normal")
    <normal 'a.txt'>

    """

    __slots__ = "name relpath path base state".split()
    
    def __init__(self, name, state, base=None):
        self.relpath = name
        self.path = dirname(name)
        self.name = basename(name)
        self.base = base
        self.state = intern(state)

    def __repr__(self):
        return "<%s %r>"%(
                self.state,
                self.relpath,
                )

    def __str__(self):
        return self.relpath

    @property
    def abspath(self):
        """
        returns the absolute path if the base is known
        else it returns None

        >>> StatedPath("a",None,"b").abspath
        "a/b"

        >>> StatedPath("a",None).abspath
        None
        """
        if self.base is not None:
            return join(self.base, self.relpath)
