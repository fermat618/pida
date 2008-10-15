# -*- coding: utf-8 -*-

"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

List of general Language classes.

"""

UNKNOWN, INFO, WARNING, ERROR = 0, 1, 2, 3

UNKNOWN = 0
ATTRIBUTE = 1
CLASS = 2
METHOD = 3
FUNCTION = 4
MODULE = 5
PROPERTY = 6
EXTRAMETHOD = 7
VARIABLE = 8
IMPORT = 9
PARAMETER = 10
BUILTIN = 11
KEYWORD = 12

class InitObject(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)



class ValidationError(InitObject):
    """Message a Validator should return"""
    message = ''
    message_args = ()
    type = UNKNOWN
    filename = None
    ineno = None

    def __str__(self):
        return '%s:%s: %s' % (self.filename, self.lineno, self.message % self.message_args)

    @staticmethod
    def from_exception(exc):
        """Returns a new Message from a python exception"""
        # FIXME
        pass


class Definition(InitObject):
    """Returned by a Definer instance"""
    file_name = None
    offset = None
    length = None
    line = None
    signature = None
    doc = None

    def __repr__(self):
        where = ""
        if self.offset is not None:
            where = " offset %s " %self.offset
        elif self.line is not None:
            where = " line %s " %self.line
        return '<Definition %s%s>' %(self.file_name, where)


class Suggestion(unicode):
    """
    Suggestions are returned by an Completer class
    """
    type_ = UNKNOWN
    doc = None
    docpath = None
    signature = None
    # content is the full text of snippet for example
    content = None

class Documentation(InitObject):
    """
    Documentation of a object in the text
    """
    path = None
    short = None
    long_ = None

    def __unicode__(self):
        return self.long_ or self.short or ""

    def __nonzero__(self):
        # a documentation object is true if it holds any value
        return bool(self.path) or bool(self.short) or bool(self.long_)
