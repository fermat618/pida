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
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, LANG_PRIO,
    Suggestion, Definition, ValidationError, Documentation)




class BaseDocumentHandler(object):

    priority = LANG_PRIO.DEFAULT

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

    def sync(self):
        """
        Called once in a while to write file cache if the plugin supports it
        """
        pass

    def close(self):
        """
        Called before this instance is deleted
        """
        pass

    @classmethod
    def priorty_for_document(cls, document):
        """Returns the priority this plugin will have for this document"""
        return cls.priority

class BaseCachedDocumentHandler(BaseDocumentHandler):
    def _default_cache(self, fnc):
        """
        Default implementation of outline cache.
        We cache as long as the file on disk does not change
        """
        if not self.__dict__.has_key('_cache_'):
            self._cache_ = []
            self._lastmtime_ = 0
        if not self.document.is_new:
            if self.document.modified_time != self._lastmtime_:
                self._cache_ = []
                iterf = fnc()
                if iterf is None:
                    return
                for x in fnc():
                    self._cache_.append(x)
                    yield x
                self._lastmtime_ = self.document.modified_time
            else:
                for x in self._cache_:
                    yield x
        else:
            iterf = fnc()
            if iterf is None:
                return
            for x in iterf:
                yield x


class Outliner(BaseCachedDocumentHandler):
    """
    The Outliner class is used to return a list of interessting code points
    like classes, function, methods, etc.
    It is usually shown by the Outliner window.
    """

    filter_type = ()

    def get_outline_cached(self):
        return self._default_cache(self.get_outline)

    def get_outline(self):
        raise NotImplementedError('Outliner must define get_outline')


class Validator(BaseCachedDocumentHandler):


    def get_validations_cached(self):
        return self._default_cache(self.get_validations)

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
        if not isinstance(self.svc.language_name, (tuple, list)):
            all_langs = (self.svc.language_name,)
        else:
            all_langs = self.svc.language_name
        mapping = {
            'outliner_factory':'outliner',
            'definer_factory': 'definer',
            'validator_factory': 'validator',
            'completer_factory': 'completer',
            'documentator_factory': 'documentator'
        }
        for lname in all_langs:
            if self.svc.language_info is not None:
                self.subscribe_foreign('language', 'info', lname, self.svc.language_info)

            for factory_name, feature in mapping.iteritems():
                factory = getattr(self.svc, factory_name)
                if factory is not None:
                    self.subscribe_foreign(
                        'language', feature, lname, 
                        partial(factory, self.svc),
                    )



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

class SnippetsProvider(object):

    def get_snippets(self, document):
        raise NotImplemented

class SnippetTemplate(object):
    text = ""

    def get_template(self):
        """
        Return text for inclusion.
        This may need expanding the template.
        """
        return self.text

    def get_tokens(self):
        """
        Returns a list of Text and Template Tokens
        """
        return []



