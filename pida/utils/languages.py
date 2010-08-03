# -*- coding: utf-8 -*-

"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

List of general Language classes.

"""
from .addtypes import Enumeration
from .symbols import Symbols
from .path import get_line_from_file
from .descriptors import cached_property

import itertools


#!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!! these are inter process interfaces, too                     !!!!
#!!!! don't change their order, remove or change existing entries !!!!
#!!!! you can append new entries at the end                       !!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


COMPLETER = Symbols('completer', [
    'unknown',
    'attribute',
    'class',
    'method',
    'function',
    'module',
    'property',
    'extramethod',
    'variable',
    'import',
    'parameter',
    'builtin',
    'keyword',
    'snippet',
])



VALIDATOR_KIND = Symbols('validation errors',
    ('unknown', 'syntax', 'indentation', 'undefined', 'redefined', 'badstyle',
     'duplicate', 'unused', 'fixme', 'protection', 'dangerous'))

VALIDATOR_LEVEL = Symbols('validation level',
    ('unknown', 'info', 'warning', 'error', 'fatal'))


# validation sub types

LANG_TYPES = Enumeration('LANG_TYPES',
 ('', 'UNKNOWN', 
 'ATTRIBUTE', 'BUILTIN', 'CLASS', 'DEFINE', 'ENUMERATION',
 'ENUMERATION_NAME', 'FUNCTION', 'IMPORT', 'MEMBER', 'METHOD', 'PROPERTY',
 'PROTOTYPE', 'STRUCTURE', 'SUPERMETHOD', 'SUPERPROPERTY', 'TYPEDEF', 'UNION',
 'VARIABLE', 'NAMESPACE', 'ELEMENT', 'SECTION', 'CHAPTER', 'PARAGRAPH'))

LANG_OUTLINER_TYPES = LANG_TYPES

LANG_PRIO = Enumeration('LANG_PRIORITIES',
(
    ('PERFECT', 100),
    ('VERY_GOOD', 50),
    ('GOOD', 10),
    ('DEFAULT', 0),
    ('LOW', -50),
    ('BAD', -100),
))


LANG_IMAGE_MAP = {
    LANG_TYPES.ATTRIBUTE: 'source-attribute',
    LANG_TYPES.BUILTIN: 'source-attribute',
    LANG_TYPES.CLASS: 'source-class',
    LANG_TYPES.DEFINE: 'source-define',
    LANG_TYPES.ENUMERATION: 'source-enum',
    LANG_TYPES.ENUMERATION_NAME: 'source-enumarator',
    LANG_TYPES.FUNCTION: 'source-function',
    LANG_TYPES.IMPORT: 'source-import',
    LANG_TYPES.MEMBER: 'source-member',
    LANG_TYPES.METHOD: 'source-method',
    LANG_TYPES.PROTOTYPE: 'source-interface',
    LANG_TYPES.PROPERTY: 'source-property',
    LANG_TYPES.METHOD: 'source-method',
    LANG_TYPES.SUPERMETHOD: 'source-extramethod',
    #FIXME: superproperty icon
    LANG_TYPES.SUPERPROPERTY: 'source-property',
    LANG_TYPES.TYPEDEF: 'source-typedef',
    LANG_TYPES.UNION: 'source-union',
    LANG_TYPES.VARIABLE: 'source-variable',
    LANG_TYPES.SECTION: 'source-section',
    LANG_TYPES.PARAGRAPH: 'source-paragraph',
    LANG_TYPES.NAMESPACE: 'source-namespace',
    LANG_TYPES.ELEMENT: 'source-element',
}


class InitObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


def color_to_string(color):
    """Converts a color object to a string"""
    if isinstance(color, basestring):
        return color
    # gtk color
    return color.to_string()

class ValidationError(InitObject):
    """Message a Validator should return"""
    message = ''
    message_args = None
    level = VALIDATOR_LEVEL.UNKNOWN
    kind = VALIDATOR_KIND.UNKNOWN
    filename = None
    lineno = None

    def __str__(self):
        return '%s:%s: %s' % (self.filename, self.lineno, self.message)

    def lookup_color(self, color):
        return "#000000"

    @staticmethod
    def from_exception(exc):
        """Returns a new Message from a python exception"""
        # FIXME
        pass

    def get_markup(self):
        mapping = {
            VALIDATOR_LEVEL.ERROR: 'pida-val-error',
            VALIDATOR_LEVEL.INFO: 'pida-val-info',
            VALIDATOR_LEVEL.WARNING: 'pida-val-warning',
        }
        typec = mapping.get(self.kind, 'pida-val-def')

        markup = ("""<tt><span color="%(linecolor)s">%(lineno)s</span> </tt>"""
    """<span foreground="%(typec)s" style="italic" weight="bold">%(type)s</span"""
    """>:<span style="italic">%(subtype)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno, 
                      'type': self.level.capitalize(),
                      'subtype': self.kind.capitalize(),
                      'message':self.message,
                      'linecolor': color_to_string(self.lookup_color('pida-lineno')),
                      'typec': color_to_string(typec),
                      })
        return markup
    markup = property(get_markup)



class OutlineItem(InitObject):
    """
    Outlines are returned by an Outliner class
    """
    type = LANG_TYPES.UNKNOWN
    name = ''
    parent = None
    id = None
    # the parent id is a link to the parent's id value which can be pickeled
    parent_id = None
    line = 0
    filter_type = None
    type_markup = ''

    def get_markup(self):
        return '<b>%s</b>' % self.name

    @cached_property
    def icon_name(self):
        return LANG_IMAGE_MAP.get(self.type, '')

    #XXX: these 2 hacks need tests!!!
    @property
    def sort_hack(self):
        try:
            #XXX: python only?!
            return '%s%s' % (self.options.position, self.name)
        except: #XXX: evil handling
            return self.name

    @property
    def line_sort_hack(self):
        if self.filename:
            return 'yyy%s%s' % (self.filename, self.linenumber)
        elif self.linenumber:
            return str(self.linenumber)
        else:
            return 'zzz'

class Definition(InitObject):
    """Returned by a Definer instance"""
    type = LANG_TYPES.UNKNOWN
    file_name = None
    offset = None
    length = None
    line = None
    signature = None
    doc = None

    def __repr__(self):
        where = ""
        if self.offset is not None:
            where = " offset %s " % self.offset
        elif self.line is not None:
            where = " line %s " % self.line
        return '<Definition %s%s>' % (self.file_name, where)

    @cached_property
    def icon_name(self):
        return LANG_IMAGE_MAP.get(self.type, '')

    def _get_signature(self):
        if self.line is None and self.offset is None:
            return None
        if not hasattr(self, '_signature_value'):
            self._signature_value = get_line_from_file(self.file_name,
                line=self.line, offset=self.offset)
        return self._signature_value

    def _set_signature(self, value):
        self._signature_value = value

    signature = property(_get_signature, _set_signature)

class Suggestion(unicode):
    """
    Suggestions are returned by an Completer class
    """
    type_ = COMPLETER.UNKNOWN
    doc = None
    docpath = None
    signature = None
    # content is the full text of snippet for example
    content = None

    @property
    def display(self):
        """
        Returns the best possible text to display
        """
        return self.signature or self

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

