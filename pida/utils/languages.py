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

OUTLINER = Symbols('outline',
 ('unknown',
 'attribute', 'builtin', 'class', 'define', 'enumeration',
 'enumeration_name', 'function', 'import', 'member', 'method', 'property',
 'prototype', 'structure', 'supermethod', 'superproperty', 'typedef', 'union',
 'variable', 'namespace', 'element', 'section', 'chapter', 'paragraph'))


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
    OUTLINER.ATTRIBUTE: 'source-attribute',
    OUTLINER.BUILTIN: 'source-attribute',
    OUTLINER.CLASS: 'source-class',
    OUTLINER.DEFINE: 'source-define',
    OUTLINER.ENUMERATION: 'source-enum',
    OUTLINER.ENUMERATION_NAME: 'source-enumarator',
    OUTLINER.FUNCTION: 'source-function',
    OUTLINER.IMPORT: 'source-import',
    OUTLINER.MEMBER: 'source-member',
    OUTLINER.METHOD: 'source-method',
    OUTLINER.PROTOTYPE: 'source-interface',
    OUTLINER.PROPERTY: 'source-property',
    OUTLINER.METHOD: 'source-method',
    OUTLINER.SUPERMETHOD: 'source-extramethod',
    #FIXME: superproperty icon
    OUTLINER.SUPERPROPERTY: 'source-property',
    OUTLINER.TYPEDEF: 'source-typedef',
    OUTLINER.UNION: 'source-union',
    OUTLINER.VARIABLE: 'source-variable',
    OUTLINER.SECTION: 'source-section',
    OUTLINER.PARAGRAPH: 'source-paragraph',
    OUTLINER.NAMESPACE: 'source-namespace',
    OUTLINER.ELEMENT: 'source-element',
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

    markup_string = (
        '<tt><span color="{linecolor}">{lineno}</span> </tt>'
        '<span foreground="{level_color}" style="italic" weight="bold">'
        '{level}</span>:'
        '<span style="italic">{kind}</span>\n'
        '{message}'
    )


    def __str__(self):
        return '%s:%s: %s' % (self.filename, self.lineno, self.message)

    def lookup_color(self, color):
        return "#000000"

    @staticmethod
    def from_exception(exc):
        """Returns a new Message from a python exception"""
        # FIXME
        pass


    @property
    def markup(self):
        return self.markup_string.format(**self.markup_args())

    def markup_args(self):
        mapping = {
            VALIDATOR_LEVEL.ERROR: 'pida-val-error',
            VALIDATOR_LEVEL.INFO: 'pida-val-info',
            VALIDATOR_LEVEL.WARNING: 'pida-val-warning',
        }
        typec = mapping.get(self.kind, 'pida-val-def')

        return {
            'lineno': self.lineno,
            'level': self.level.capitalize(),
            'level_color': color_to_string(typec),
            'kind': self.kind.capitalize(),
            'message': self.message,
            'linecolor': color_to_string(self.lookup_color('pida-lineno')),
        }



class OutlineItem(InitObject):
    """
    Outlines are returned by an Outliner class
    """
    type = OUTLINER.UNKNOWN
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
    type = OUTLINER.UNKNOWN
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

