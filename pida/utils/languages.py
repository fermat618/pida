# -*- coding: utf-8 -*-

"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

List of general Language classes.

"""
from .addtypes import Enumeration
from .path import get_line_from_file



#!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!! these are inter process interfaces, too                     !!!!
#!!!! don't change their order, remove or change existing entries !!!!
#!!!! you can append new entries at the end                       !!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!



# completer types
LANG_COMPLETER_TYPES = Enumeration('LANG_COMPLETER_TYPES',
    ('UNKNOWN', 'ATTRIBUTE', 'CLASS', 'METHOD', 'FUNCTION', 'MODULE', 
    'PROPERTY', 'EXTRAMETHOD', 'VARIABLE', 'IMPORT', 'PARAMETER', 'BUILTIN', 
    'KEYWORD', 'SNIPPET'))


# main types
LANG_VALIDATOR_TYPES = Enumeration('LANG_TYPES',
    ('UNKNOWN', 'INFO', 'WARNING', 'ERROR', 'FATAL'))

# validation sub types
LANG_VALIDATOR_SUBTYPES = Enumeration('LANG_VALIDATION_ERRORS',
    ('UNKNOWN', 'SYNTAX', 'INDENTATION', 'UNDEFINED', 'REDEFINED', 'BADSTYLE',
     'DUPLICATE', 'UNUSED', 'FIXME', 'PROTECTION', 'DANGEROUS'))

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
    type_ = LANG_VALIDATOR_TYPES.UNKNOWN
    subtype = LANG_VALIDATOR_SUBTYPES.UNKNOWN
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
        if self.type_ == LANG_VALIDATOR_TYPES.ERROR:
            typec = self.lookup_color('pida-val-error')
        elif self.type_ == LANG_VALIDATOR_TYPES.INFO:
            typec = self.lookup_color('pida-val-info')
        elif self.type_ == LANG_VALIDATOR_TYPES.WARNING:
            typec = self.lookup_color('pida-val-warning')
        else:
            typec = self.lookup_color('pida-val-def')
        
        markup = ("""<tt><span color="%(linecolor)s">%(lineno)s</span> </tt>"""
    """<span foreground="%(typec)s" style="italic" weight="bold">%(type)s</span"""
    """>:<span style="italic">%(subtype)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno, 
                      'type':_(LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize()),
                      'subtype':_(LANG_VALIDATOR_SUBTYPES.whatis(
                                    self.subtype).capitalize()),
                      'message':self.message,
                      'linecolor': color_to_string(self.lookup_color('pida-lineno')),
                      'typec': color_to_string(typec),
                      })
        return markup
    markup = property(get_markup)
#     def get_markup(self):
#         #args = [('<b>%s</b>' % arg) for arg in msg.message_args]
#         #message_string = self.message % tuple(args)
#         #msg.name = msg.__class__.__name__
#         markup = ('<tt>%s </tt><i>%s:%s</i>\n%s' % 
#                       (self.lineno, 
#                       LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize(),
#                       LANG_VALIDATOR_SUBTYPES.whatis(self.subtype).capitalize(),
#                       self.message))
#         return markup
#     
#     markup = property(get_markup)




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

    def _get_icon_name(self):
        return getattr(self, '_icon_name_set', 
                                    LANG_IMAGE_MAP.get(self.type, ''))
    def _set_icon_name(self, value):
        self._icon_name_set = value
    icon_name = property(_get_icon_name, _set_icon_name)

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

    def _get_icon_name(self):
        return getattr(self, '_icon_name_set', 
                                    LANG_IMAGE_MAP.get(self.type, ''))
    def _set_icon_name(self, value):
        self._icon_name_set = value

    icon_name = property(_get_icon_name, _set_icon_name)

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
    type_ = LANG_TYPES.UNKNOWN
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
        if self.signature:
            return self.signature
        return self

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

