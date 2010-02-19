# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
Language Support Superclasses

:license: GPL2 or later
:copyright: 2008 the Pida Project
"""
from functools import partial
from weakref import WeakKeyDictionary
import gobject

from pida.core.document import Document

from pida.core.projects import Project
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.environment import opts
from pida.utils.languages import (LANG_COMPLETER_TYPES,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, LANG_PRIO,
    Suggestion, Definition, ValidationError, Documentation)
from pida.utils.path import get_relative_path
# locale
from pida.core.locale import Locale
locale = Locale('core')
_ = locale.gettext

from pida.core.log import get_logger, Log
log = get_logger('core.languages')

if opts.multiprocessing:
    try:
        import multiprocessing
        from multiprocessing.managers import (BaseManager, BaseProxy,
            SyncManager, RemoteError)

#         does not detect work yet :-(
#         class TestResult(object):
#             def __init__(self, i):
#                 self.i = i
#
#         class TestManager(BaseManager):
#             @staticmethod
#             def test():
#                 for i in (TestResult(1), TestResult(2)):
#                     yield i
#
#         m = TestManager()
#         m.start()
#         for i in m.test():
#             print i
#         m.shutdown()

    except ImportError:
        log.info(_("Can't find multiprocessing, disabled work offload"))
        multiprocessing = None
        BaseManager = BaseProxy = SyncManager = object
        class RemoteError(Exception):
            pass
else:
    multiprocessing = None
    BaseManager = BaseProxy = SyncManager = object
    class RemoteError(Exception):
        pass

#FIXME: maybe we should fill the plugin values with a metaclass ???
# class LanguageMetaclass(type):
#     def __new__(meta, name, bases, dct):
#         print "Creating class %s using CustomMetaclass" % name
#         print meta, name, bases, dct
#         klass = type.__new__(meta, name, bases, dct)
#         #meta.addParentContent(klass)
#         klass.plugin = dct['__module__']
#         return klass

# priorities for running language plugins

PRIO_DEFAULT = gobject.PRIORITY_DEFAULT_IDLE + 100
PRIO_FOREGROUND = PRIO_DEFAULT - 40

PRIO_FOREGROUND_HIGH = PRIO_FOREGROUND - 40

PRIO_LOW = PRIO_DEFAULT + 40


class BaseDocumentHandler(object):
    """
    Base class for all language plugins
    """

    #__metaclass__ = LanguageMetaclass
    priority = LANG_PRIO.DEFAULT
    name = "NAME MISSING"
    plugin = "PLUGIN MISSING"
    description = "DESCRIPTION MISSING"

    def __init__(self, svc, document=None):
        self.svc = svc
        self.set_document(document)


    @classmethod
    def uuid(cls):
        """
        Returns a unique id for this class as a string to identify it again
        """
        return "%s.%s" % (cls.__module__, cls.__name__)

    @property
    def uid(self):
        """
        property for uuid()
        """
        return self.__class__.uuid()

    def set_document(self, document):
        """
        sets the document this instance is assigned to
        """
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
    """
    Default cache implementation for Languge Plugins.

    The cache is valid until the file is changed on disk
    """

    def _default_cache(self, fnc):
        """
        Default implementation of outline cache.
        We cache as long as the file on disk does not change
        """
        if not hasattr(self, '_cache'):
            self._cache = []
            self._lastmtime = 0
        if not self.document.is_new:
            if self.document.modified_time != self._lastmtime:
                self._cache = []
                iterf = fnc()
                if iterf is None:
                    return
                for x in fnc():
                    self._cache.append(x)
                    yield x
                self._lastmtime = self.document.modified_time
            else:
                for x in self._cache:
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
        """
        Returns a cached iterator of OutlineItems
        """
        return self._default_cache(self.get_outline)

    def get_outline(self):
        """
        Returns a fresh computed iterator of OutlineItems
        """
        raise NotImplementedError('Outliner must define get_outline')


class Validator(BaseCachedDocumentHandler):


    def get_validations_cached(self):
        """
        Returns a cached iterator of ValidatorItems
        """
        return self._default_cache(self.get_validations)

    def get_validations(self):
        """
        Returns a fresh computed iterator of ValidatorItems
        """
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
        raise NotImplementedError('Definer must define get_definition')

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
        raise NotImplementedError('Documentator must define get_definition')

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
                     ['_', ]
    varchars = [chr(x) for x in xrange(97, 122)] + \
               [chr(x) for x in xrange(65, 90)] + \
               [chr(x) for x in xrange(48, 58)] + \
               ['_', ]

    word = varchars
    word_first = varchars_first

    open_backets = ['[', '(', '{']
    close_backets = [']', ')', '}']

    # . in python; -> in c, ...
    attributerefs = []

    completer_open = ['[', '(', '{']
    completer_close = [']', ')', '}']

    keywords = []
    operators = []

    comment_line = []
    comment_start = []
    comment_end = []

    # i think most languages are
    case_sensitive = True

    def __init__(self, document):
        self.document = document

    def to_dbus(self):
        return {'varchars':      self.varchars,
                'word':          self.word,
                'attributerefs': self.attributerefs,
               }

class TooManyResults(Exception):
    """
    Indicates that the Outliner had to many suggestions returned.

    This will cause the cache to be cleared and will cause a rerun of the
    get_outliner on the next character entered

    @base: base string used
    @expect_length: integer of additional characters needed so the Exception
                    won't happen again
    """
    def __init__(self, base, expected_length=None):
        super(TooManyResults, self).__init__()
        self.base = base
        if expected_length is None:
            self.expected_length = len(base) + 1
        else:
            self.expected_length = expected_length


class Completer(BaseDocumentHandler):
    """
    Completer returns suggestions for autocompleter features
    """

    def get_completions(self, base, buffer_, offset):
        """
        Gets a list of completitions.

        @base - string which starts completions
        @buffer - document to parse
        @offset - cursor position
        """
        raise NotImplementedError('Completer must define get_completions')


def make_iterable(inp):
    if not isinstance(inp, (tuple, list)) and not hasattr(inp, '__iter__'):
        return (inp,)
    return inp


class LanguageServiceFeaturesConfig(FeaturesConfig):
    """
    An advanced version of FeaturesConfig used for language plugins.

    Please remember to call the overloaded function
    """

    def subscribe_all_foreign(self):
        all_langs = make_iterable(self.svc.language_name)
        mapping = {
            'outliner_factory': 'outliner',
            'definer_factory': 'definer',
            'validator_factory': 'validator',
            'completer_factory': 'completer',
            'documentator_factory': 'documentator'
        }
        # register all language info classes
        for lname in all_langs:
            if self.svc.language_info is not None:
                self.subscribe_foreign('language', 'info', lname,
                                       self.svc.language_info)


        for factory_name, feature in mapping.iteritems():
            factory = getattr(self.svc, factory_name)
            if factory is not None:
                # a language_name of a factory overrides the service
                # language_name
                if hasattr(factory, 'language_name'):
                    cur_langs = make_iterable(factory.language_name)
                else:
                    cur_langs = all_langs
                for lname in cur_langs:
                    self.subscribe_foreign(
                            'language', feature, lname,
                            partial(factory, self.svc))


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



# Proxy type for generator objects
class GeneratorProxy(BaseProxy):
    """
    Proxies iterators over multiprocessing
    """
    _exposed_ = ('next', '__next__')
    def __iter__(self):
        return self
    def next(self):
        try:
            return self._callmethod('next')
        except (RemoteError, EOFError):
            if getattr(self._manager, 'is_shutdown', False):
                raise StopIteration
            else:
                raise

    def __next__(self):
        try:
            return self._callmethod('__next__')
        except (RemoteError, EOFError):
            if getattr(self._manager, 'is_shutdown', False):
                raise StopIteration
            else:
                raise

class ExternalMeta(type):
    """
    MetaClass for Extern classes. registers the functions for beeing extern
    callable
    """
    LANG_MAP = {
        'validator': ['get_validations'],
        'outliner': ['get_outline'],
        'completer': ['get_completions'],
        'documentator': ['get_documentation'],
        'definer': ['get_definition'],
      }
    def __new__(cls, name, bases, dct):
        return type.__new__(cls, name, bases, dct)
    def __init__(cls, name, bases, dct):
        super(ExternalMeta, cls).__init__(name, bases, dct)
        if not hasattr(cls, 'register'):
            return
        for type_, funcs in cls.LANG_MAP.iteritems():
            if not type_ in dct or not dct[type_]:
                continue
            cls.register(type_, dct[type_])
            for mfunc in funcs:
                nname = "%s_%s" % (type_, mfunc)
                # we register the function as a callable external
                cls.register(nname, getattr(dct[type_], mfunc), proxytype=GeneratorProxy)


class External(SyncManager):
    """
    The External superclass is used to configure and control the external
    processes.

    Create a new class inhereting from External and define the class
    variables of the types you want to externalize. This class must be the
    'extern' class variable of your LanguageService

    @validator: validator class
    @outliner
    @definer
    @documentator

    You can define additional static functions here that can be run on the
    external process.
    """

    __metaclass__ = ExternalMeta

    validator = None
    outliner = None
    definer = None
    documentator = None
    definer = None
    completer = None

    @staticmethod
    def validator_get_validations(instance):
        for i in instance.get_validations():
            yield i

    @staticmethod
    def outliner_get_outline(instance):
        for i in instance.get_outline():
            yield i

    @staticmethod
    def definer_get_definition(instance, buffer, offset):
        for i in instance.get_definition(buffer, offset):
            yield i

    @staticmethod
    def documentator_get_documentation(instance, buffer, offset):
        for i in instance.get_documentation(buffer, offset):
            yield i

class ExternalDocument(Document):
    """
    Emulates a document that resides in a different python process
    """
    _unique_id = 0
    _project_path = None
    _project = None

    @property
    def uniqueid(self):
        return self._unique_id

    def get_project_relative_path(self):
        """
        Returns the relative path to Project's root
        """
        if self.filename is None or not self._project_path:
            return None, None
        return get_relative_path(self._project_path, self.filename)

    def _get_project(self):
        # test if the path changed and forget the old project
        if self._project and self._project.source_directory != self._project_path:
            self._project = None
        if self._project:
            return self._project
        if self._project_path:
            self._project = Project(self._project_path)
            return self._project

    def _set_project(self, value):
        pass
    project = property(_get_project, _set_project)

class ExternalProxy(object):
    """
    Base Class for all proxy objects.
    """
    _external_document = None

    def set_document(self, document):
        self.document = document
        self._external_document = None

    def get_external_document(self):
        if not self._external_document:
            self._external_document = ExternalDocument(None, self.document.filename)
            self._external_document._unique_id = self.document.unique_id
            if self.document.project:
                self._external_document._project_path = self.document.project.source_directory
        return self._external_document

    @classmethod
    def uuid(cls):
        return cls._uuid

    @property
    def uid(self):
        """
        property for uuid()
        """
        return self._uuid

class ExternalValidatorProxy(ExternalProxy, Validator):
    """Proxies to the jobmanager and therefor to the external process"""
    def get_validations(self):
        for result in self.svc.jobserver.validator_get_validations(self):
            yield result

class ExternalOutlinerProxy(ExternalProxy, Outliner):
    """Proxies to the jobmanager and therefor to the external process"""
    def get_outline(self):
        for result in self.svc.jobserver.outliner_get_outline(self):
            yield result

class ExternalDefinerProxy(ExternalProxy, Definer):
    """Proxies to the jobmanager and therefor to the external process"""
    def get_definition(self, buffer, offset):
        rv = self.svc.jobserver.definer_get_definition(self, buffer, offset)
        if hasattr(rv, '__iter__'):
            for result in rv:
                yield result
        else:
            yield rv

class ExternalDocumentatorProxy(ExternalProxy, Documentator):
    """Proxies to the jobmanager and therefor to the external process"""
    def get_documentation(self, buffer, offset):
        rv = self.svc.jobserver.documentator_get_documentation(self, buffer,
                                                               offset)
        if hasattr(rv, '__iter__'):
            for result in rv:
                yield result
        else:
            yield rv

class ExternalCompleterProxy(ExternalProxy, Completer):
    """Proxies to the jobmanager and therefor to the external process"""
    def get_completions(self, base, buffer_, offset):
        rv = self.svc.jobserver.completer_get_completions(self, base,
                                                          buffer_, offset)
        if hasattr(rv, '__iter__'):
            for result in rv:
                yield result
        else:
            yield rv

class Merger(BaseDocumentHandler):
    """
    Merges different sources of providers into one stream
    """
    def __init__(self, svc, document=None, sources=()):
        self.set_sources(sources)
        super(Merger, self).__init__(svc, document)

    def set_sources(self, sources):
        """
        Set all sources that will be used to build the results.

        The order of the sources will define the order which create the results
        """
        self.sources = sources
        self.instances = None

    def create_instances(self):
        """
        Create all instances that are an the sources list
        """
        self.instances = []
        for factory in self.sources:
            handler = factory(self.document)
            if handler:
                self.instances.append(handler)


class MergeCompleter(Completer, Merger):
    def get_completions(self, base, buffer_, offset):
        if not self.instances:
            self.create_instances()
        results = set()
        for prov in self.instances:
            for res in prov.get_completions(base, buffer_, offset):
                if res in results:
                    continue
                results.add(res)
                yield res

def safe_remote(func):
    def safe(self, *args, **kwargs):
        try:
            for i in func(self, *args, **kwargs):
                yield i
        except RuntimeError, e:
            log.warning(_("problems running external plugin: %s"), e)
            self.restart()
            return
        except:
            if self.stopped:
                return
            raise
    return safe


class JobServer(Log):
    """
    The Jobserver dispatches language plugin jobs to external processes it
    manages.
    """
    def __init__(self, svc, external, max_processes=2):
        self.svc = svc
        self.max_processes = max_processes
        self.stopped = False
        # we have to map the proxy objects to
        self._external = external
        self._processes = []
        self._proxy_map = WeakKeyDictionary()
        self._instances = {}

    def get_process(self, proxy=None):
        """
        Returns a Extern instance.
        It tries to use the same instance for proxy so it does not need to
        be recreated and can make best use of caching
        """
        #FIXME needs some better management of processes and dispatching
        if not self._processes:
            np = self._external()
            np.start()
            self._instances[np] = {} #np.dict()
            self._processes.append(np)
        return self._processes[0]

    def get_instance(self, proxy, type_):
        """
        Returns the manager and the real instance of language plugin type of
        the proxy.

        Everything called on this objects are done in the external process
        """
        manager = self._proxy_map.get(proxy, None)
        if not manager:
            manager = self.get_process(proxy)
            self._proxy_map[proxy] = manager
        instances = self._instances[manager]
        if proxy.document.unique_id not in instances:
            instances[proxy.document.unique_id] = manager.dict()
        if type_ not in instances[proxy.document.unique_id]:
            #no = getattr(manager, type_)(manager)(None, proxy.document)
            instances[proxy.document.unique_id][type_] = getattr(manager, type_)(None, proxy.get_external_document())
        return manager, instances[proxy.document.unique_id][type_]

    @safe_remote
    def validator_get_validations(self, proxy):
        """Forwards to the external process"""
        manager, instance = self.get_instance(proxy, 'validator')
        for i in manager.validator_get_validations(instance):
            yield i

    @safe_remote
    def outliner_get_outline(self, proxy):
        """Forwards to the external process"""
        manager, instance = self.get_instance(proxy, 'outliner')
        for i in manager.outliner_get_outline(instance):
            yield i

    @safe_remote
    def definer_get_definition(self, proxy, buffer, offset):
        """Forwards to the external process"""
        manager, instance = self.get_instance(proxy, 'definer')
        for i in manager.definer_get_definition(instance, buffer, offset):
            yield i

    @safe_remote
    def documentator_get_documentation(self, proxy, buffer, offset):
        """Forwards to the external process"""
        manager, instance = self.get_instance(proxy, 'documentator')
        for i in manager.documentator_get_documentation(instance, buffer,
                                                        offset):
            yield i

    @safe_remote
    def completer_get_completions(self, proxy, base, buffer, offset):
        """Forwards to the external process"""
        manager, instance = self.get_instance(proxy, 'completer')
        for i in manager.completer_get_completions(instance, base, buffer,
                                                        offset):
            yield i

    def stop(self):
        self.stopped = True
        for i in self._processes:
            i.is_shutdown = True
            i.shutdown()

    def restart(self):
        self.log.info(_("restart jobserver"))
        self.stop()
        self.stopped = False
        self._processes = []
        self._proxy_map = WeakKeyDictionary()
        self._instances = {}


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

    external = None
    jobserver_factory = JobServer

    features_config = LanguageServiceFeaturesConfig

    def __init__(self, boss):
        if self.external is not None and multiprocessing:
            # if we have multiprocessing support we exchange the
            # language factories to the proxy objects
            def newproxy(old, factory):
                class NewProxy(factory):
                    pass
                NewProxy._uuid = old.uuid()
                NewProxy.priority = old.priority
                NewProxy.name = old.name
                NewProxy.plugin = old.plugin
                NewProxy.description = old.description
                return NewProxy

            if self.external.validator:
                self.validator_factory = newproxy(self.validator_factory, ExternalValidatorProxy)
            if self.external.outliner:
                ofac = self.outliner_factory
                self.outliner_factory = newproxy(self.outliner_factory, ExternalOutlinerProxy)
                self.outliner_factory.filter_type = ofac.filter_type
            if self.external.documentator:
                self.documentator_factory = newproxy(self.documentator_factory, ExternalDocumentatorProxy)
            if self.external.definer:
                self.definer_factory = newproxy(self.definer_factory, ExternalDefinerProxy)
            if self.external.completer:
                self.completer_factory = newproxy(self.completer_factory, ExternalCompleterProxy)

        super(LanguageService, self).__init__(boss)
        self.boss = boss
        if self.external is not None and multiprocessing:
            self.jobserver = self.jobserver_factory(self, self.external)
        else:
            self.jobserver = None

    def stop(self):
        if self.jobserver:
            self.jobserver.stop()
        super(LanguageService, self).stop()

LANGUAGE_PLUGIN_TYPES = {
'completer': {
    'name': _('Completer'),
    'description': _('Provides suggestions for autocompletion'),
    'class': Completer},
'definer': {
    'name': _('Definer'),
    'description': _(
        'Jumps to the code position where the current symbol is defined'),
    'class': Definer},
'documentator': {
    'name': _('Documentator'),
    'description': _('Provides the signature of the current symbol'),
    'class': Documentator},
'outliner': {
    'name': _('Outliner'),
    'description': _('Provides informations where symbols are defined'),
    'class': Outliner},
'validator': {
    'name': _('Validator'),
    'description': _('Shows problems and style errors in the code'),
    'class': Validator}
}

