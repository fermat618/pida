# -*- coding: utf-8 -*-

"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

List of general Language classes.

"""
from .addtypes import Enumeration

# completer types
LANG_COMPLETER_TYPES = Enumeration('LANG_COMPLETER_TYPES',
    ('UNKNOWN', 'ATTRIBUTE', 'CLASS', 'METHOD', 'FUNCTION', 'MODULE', 'PROPERTY',
    'EXTRAMETHOD', 'VARIABLE', 'IMPORT', 'PARAMETER', 'BUILTIN', 
    'KEYWORD', 'SNIPPET'))


# main types
LANG_VALIDATOR_TYPES = Enumeration('LANG_TYPES',
    ('UNKNOWN', 'INFO', 'WARNING', 'ERROR', 'FATAL'))

# validation sub types
LANG_VALIDATOR_SUBTYPES = Enumeration('LANG_VALIDATION_ERRORS',
    ('UNKNOWN', 'SYNTAX', 'INDENTATION', 'UNDEFINED', 'REDEFINED', 'BADSTYLE',
     'DUPLICATE', 'UNUSED'))

# validation sub types

LANG_OUTLINER_TYPES = Enumeration('LANG_OUTLINER_TYPES',
 ('', 'UNKNOWN', 
 'ATTRIBUTE', 'BUILTIN', 'CLASS', 'DEFINE', 'ENUMERATION',
 'ENUMERATION_NAME', 'FUNCTION', 'IMPORT', 'MEMBER', 'METHOD', 'PROPERTY',
 'PROTOTYPE', 'STRUCTURE', 'SUPERMETHOD', 'SUPERPROPERTY', 'TYPEDEF', 'UNION',
 'VARIABLE'))

LANG_PRIO = Enumeration('LANG_PRIORITIES',
(
    ('PERFECT', 100),
    ('VERY_GOOD', 50),
    ('GOOD', 10),
    ('DEFAULT', 0),
    ('LOW', -50),
    ('BAD', -100),
))


LANG_OUTLINE_IMAGE_MAP = {
    LANG_OUTLINER_TYPES.ATTRIBUTE: 'source-attribute',
    LANG_OUTLINER_TYPES.BUILTIN: 'source-attribute',
    LANG_OUTLINER_TYPES.CLASS: 'source-class',
    LANG_OUTLINER_TYPES.DEFINE: 'source-define',
    LANG_OUTLINER_TYPES.ENUMERATION: 'source-enum',
    LANG_OUTLINER_TYPES.ENUMERATION_NAME: 'source-enumarator',
    LANG_OUTLINER_TYPES.FUNCTION: 'source-function',
    LANG_OUTLINER_TYPES.IMPORT: 'source-import',
    LANG_OUTLINER_TYPES.MEMBER: 'source-member',
    LANG_OUTLINER_TYPES.METHOD: 'source-method',
    LANG_OUTLINER_TYPES.PROTOTYPE: 'source-interface',
    LANG_OUTLINER_TYPES.PROPERTY: 'source-property',
    LANG_OUTLINER_TYPES.METHOD: 'source-method',
    LANG_OUTLINER_TYPES.SUPERMETHOD: 'source-extramethod',
    #FIXME: superproperty icon
    LANG_OUTLINER_TYPES.SUPERPROPERTY: 'source-property',
    LANG_OUTLINER_TYPES.TYPEDEF: 'source-typedef',
    LANG_OUTLINER_TYPES.UNION: 'source-union',
    LANG_OUTLINER_TYPES.VARIABLE: 'source-variable',
}



class InitObject(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)


class ValidationError(InitObject):
    """Message a Validator should return"""
    message = ''
    type = LANG_VALIDATOR_TYPES.UNKNOWN
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
                      'linecolor': self.lookup_color('pida-lineno').to_string(),
                      'typec': typec.to_string(),
                      })
        return markup
    markup = property(get_markup)
    def get_markup(self):
        #args = [('<b>%s</b>' % arg) for arg in msg.message_args]
        #message_string = self.message % tuple(args)
        #msg.name = msg.__class__.__name__
        markup = ('<tt>%s </tt><i>%s:%s</i>\n%s' % 
                      (self.lineno, 
                      LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize(),
                      LANG_VALIDATOR_SUBTYPES.whatis(self.subtype).capitalize(),
                      self.message))
        return markup
    
    markup = property(get_markup)




class OutlineItem(InitObject):
    """
    Outlines are returned by an Outliner class
    """
    type = LANG_OUTLINER_TYPES.UNKNOWN
    name = ''
    parent = None
    line = 0
    filter_type = None

    def get_markup(self):
        return '<b>%s</b>' % self.name

    def _get_icon_name(self):
        return getattr(self, '_icon_name_set', 
                                    LANG_OUTLINE_IMAGE_MAP.get(self.type, ''))
    def _set_icon_name(self, value):
        self._icon_name_set = value
    icon_name = property(_get_icon_name, _set_icon_name)


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
    type_ = LANG_COMPLETER_TYPES.UNKNOWN
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

