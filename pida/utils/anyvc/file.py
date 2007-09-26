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

    >>> StatedPath('a.txt')
    <normal 'a.txt'>
    >>> StatedPath('a.txt', 'changed')
    <changed 'a.txt'>

    """

    __slots__ = 'name', 'relpath', 'path', 'base', 'state'
    
    def __init__(self, name, state='normal', base=None):
        self.relpath = name
        self.path = dirname(name)
        self.name = basename(name)
        self.base = base
        self.state = intern(state)

    def __repr__(self):
        return '<%s %r>'%(
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

        >>> StatedPath('a', base='b').abspath
        'b/a'

        >>> StatedPath('a').abspath
        
        """
        if self.base is not None:
            return join(self.base, self.relpath)
