# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
Language Support Superclasses

:license: GPL2 or later
:copyright: 2008 the Pida Project
"""
from functools import partial

from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.utils.languages import (LANG_COMPLETER_TYPES,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES,
    Suggestion, Definition, ValidationError, Documentation)

PRIO_PERFECT = 100
PRIO_VERY_GOOD = 50
PRIO_GOOD = 10
PRIO_DEFAULT = 0
PRIO_LOW = -50
PRIO_BAD = -100


class BaseDocumentHandler(object):

    priority = PRIO_DEFAULT

    def __init__(self, svc, document=None):
        self.svc = svc
        self.set_document(document)

    def set_document(self, document):
        self.document = document

    def __cmp__(self, other):
        # We do a reverse default ordering. Higher the number lower the item
        if isinstance(other, BaseDocumentHandler):
            return -1 * self.priority.__cmp__(other.priority)

        # what to do, what to do...
        return -1 * super(BaseDocumentHandler).__cmp__(other)

    @classmethod
    def priorty_for_document(cls, document):
        """Returns the priority this plugin will have for this document"""
        return cls.priority


class Outliner(BaseDocumentHandler):

    def __init__(self,svc,document=None):
        BaseDocumentHandler.__init__(self,svc,document)
        self.filter = {}

    def switch_filter(self,f):
        self.filter[f] = not self.filter[f]

    def get_outline_filtered(self):
        for (node,parent) in self.get_outline():
            if node.filter_type in self.filter:
                if self.filter[node.filter_type]:
                    yield (node,parent)
                else:
                    pass
            else:
                yield (node,parent)

    
    def get_outline(self):
        raise NotImplementedError('Outliner must define get_outline')


class Validator(BaseDocumentHandler):

    def get_validations(self):
        raise NotImplementedError('Validator must define get_validations')

class Definer(BaseDocumentHandler):
    """
    The definer class is used to allow the user to the definition of a
    word.
    """
    def get_definition(self, buffer, offset):
        """
        Returns the Definition class pointing to document defining the word
        searched for. The Definier has to find out which word the offset is on.

        @buffer - the text to search in
        @offset - nth char in the document point is on
        """
        raise NotImplementedError('Validator must define get_definition')

class Documentator(BaseDocumentHandler):
    """
    Documentation receiver returns a Documentation object
    """

    def get_documentation(self, buffer, offset):
        """
        Returns the Documentation object for a offset of an file.

        @buffer - the text to search in
        @offset - nth char in the document point is on
        """
        raise NotImplementedError('Validator must define get_definition')

class LanguageInfo(object):
    """
    LanguageInfo class stores and transports general informations.

    @varchars - list of characters which can be used in a variable
    @word - characters not in word let the editor detect on of suggestions
    @attributrefs - characters used to show char to access attributes of objects
    """
    # variable have usually only chars a-zA-Z0-9_
    # the first character of variables have an own list
    varchars_first = [chr(x) for x in xrange(97, 122)] + \
                     [chr(x) for x in xrange(48, 58)] + \
                     ['_',]
    varchars = [chr(x) for x in xrange(97, 122)] + \
               [chr(x) for x in xrange(65, 90)] + \
               [chr(x) for x in xrange(48, 58)] + \
               ['_',]

    word = varchars
    word_first = varchars_first

    open_backets = ['[','(','{']
    close_backets = [']',')','}']

    # . in python; -> in c, ...
    attributerefs = []

    def __init__(self, document):
        self.document = document

    def to_dbus(self):
        return {'varchars':      self.varchars,
                'word':          self.word,
                'attributerefs': self.attributerefs,
               }

class Completer(BaseDocumentHandler):

    def get_completions(self, base, buffer, offset):
        """
        Gets a list of completitions.
        
        @base - string which starts completions
        @buffer - document to parse
        @offset - cursor position
        """
        raise NotImplementedError('Validator must define get_completions')


class LanguageServiceFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        if self.svc.language_info is not None:
            self.subscribe_foreign('language',
                (self.svc.language_name, 'info'), self.svc.language_info)
        if self.svc.outliner_factory is not None:
            outliner = partial(self.svc.outliner_factory,self.svc)
            self.subscribe_foreign('language',
                (self.svc.language_name, 'outliner'), outliner)
        if self.svc.definer_factory is not None:
            definer = partial(self.svc.definer_factory,self.svc)
            self.subscribe_foreign('language',
                (self.svc.language_name, 'definer'), definer)
        if self.svc.validator_factory is not None:
            validator = partial(self.svc.validator_factory,self.svc)
            self.subscribe_foreign('language',
                (self.svc.language_name, 'validator'), validator)
        if self.svc.completer_factory is not None:
            completer = partial(self.svc.completer_factory,self.svc)
            self.subscribe_foreign('language',
                (self.svc.language_name, 'completer'), completer)
        if self.svc.documentator_factory is not None:
            documentator = partial(self.svc.documentator_factory,self.svc)
            self.subscribe_foreign('language',
                (self.svc.language_name, 'documentator'), documentator)



class LanguageService(Service):
    """
    Base class for easily implementing a language service
    """

    language_name = None
    language_info = None
    completer_factory = None
    definer_factory = None
    outliner_factory = None
    validator_factory = None
    documentator_factory = None

    features_config = LanguageServiceFeaturesConfig

    def pre_start(self):
        if self.language_name is None:
            raise NotImplementedError('Language services must specify a language.')


