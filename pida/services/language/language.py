# -*- coding: utf-8 -*- 
"""
    pida.services.languages
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies support for languages

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL2 or later
"""

from functools import partial

import gtk

from pida.core.doctype import DocType
from pida.core.languages import LanguageInfo

from pida.utils.gthreads import gcall
#from pida.utils.languages import LANG_OUTLINER_TYPES
from pida.utils.addtypes import PriorityList

# core
#from pida.core.service import Service
from pida.core.languages import (LanguageService, LanguageServiceFeaturesConfig,
                                 MergeCompleter)
from pida.core.events import EventsConfig
from pida.core.actions import (ActionsConfig, TYPE_TOGGLE,
                               TYPE_REMEMBER_TOGGLE, TYPE_MENUTOOL, TYPE_NORMAL)
from pida.core.options import OptionsConfig
#from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.log import get_logger
from pida.utils.languages import Definition

# ui


from pida.ui.prioritywindow import Category
from pida.ui.views import WindowConfig

from .disabled import (NoopCompleter, NoopValidator, NoopDefiner, 
                       NoopDocumentator, NoopOutliner)

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

logger = get_logger('service.language')

LEXPORT = EXPORT(suffix='language')

# we have to put our type database here, as plugins may need it long before
# registering
from .__init__ import DOCTYPES
from .gui import (ValidatorView, BrowserView, LanguageEntry,
                 LanguagePriorityView, DefinitionView)

def get_value(tab, key):
    return tab.get(key, None)


class SimpleLanguageMapping(dict):
    """
    this maps language features
    it wont handle priorities 
    """
    def get_or_create(self, language):
        if language not in self:
            self[language] = list()
        return self[language]

    def add(self, language, instance):
        self.get_or_create(language)

        self[language].append(instance)

    def remove(self, language, instance):
        self[language].remove(instance)


class PriorityLanguageMapping(dict):
    """
    this maps language features.
    Sorts it's members after their priority member
    """
    def get_or_create(self, language):
        if language not in self:
            self[language] = list()
        return self[language]

    def add(self, language, instance):
        self.get_or_create(language)

        self[language].append(instance)

        def get_prio(elem):
            if hasattr(elem, 'priority'):
                return elem.priority

        self[language].sort(key=get_prio, reverse=True)

    def remove(self, language, instance):
        self[language].remove(instance)


class CustomLanguagePrioList(PriorityList, Category):
    def get_keyfnc(self, default=True):
        def getkey(item):
            if isinstance(item, partial):
                return item.func.uuid()
            return item.uuid()
        def getprio(item):
            if isinstance(item, partial) and hasattr(item.func, 'priority'):
                return item.func.priority*-1
            elif hasattr(item, 'priority'):
                return item.priority*-1
        if self.customized and default:
            return getkey
        return getprio
    def set_keyfunc(self, value):
        pass
    _keyfnc = property(get_keyfnc, set_keyfunc)

    @property
    def _keyfnc_default(self):
        return self.get_keyfnc(default=False)

    def _sort_iterator(self):
        for x in self._sort_list:
            yield x['uuid']

    def set_sort_list(self, sort_list):
        self.customized = bool(sort_list)
        super(CustomLanguagePrioList, self).set_sort_list(sort_list)

    def update_sort_list(self):
        lst = []
        added = set()
        for x in self:
            if x.uuid() in added:
                continue
            lst.append({"uuid": x.uuid(),
                        "name": x.name,
                        "plugin": x.plugin,
                        "description": x.description})
            added.add(x.uuid())

        self.set_sort_list(lst)

    def get_full_list(self):
        if self._sort_list:
            rv = []
            done = []
            uplst = dict((x.uuid(), x) for x in self)
            for i in self.get_sort_list():
                uid = i['uuid']
                name = i['name']
                plugin = i['plugin']
                description = i['description']
                # if the plugin is loaded, we can get up to date
                # data from it
                if uplst.has_key(uid):
                    name = uplst[uid].name
                    description = uplst[uid].description
                    plugin = uplst[uid].plugin
                le = LanguageEntry(uuid=i['uuid'], name=name,
                         plugin=plugin, description=description)
                done.append(i['uuid'])
                rv.append(le)
            for i in self:
                if i.uuid() in done:
                    continue
                le = LanguageEntry.from_plugin(i)
                rv.append(le)
            return rv
        else:
            return [LanguageEntry.from_plugin(i) for i in self]

    def get_joined(self, other_lists=()):
        """
        Returns the best element possible.
        
        This may be the sort_list defined or according to priority
        
        @other_lists: other CustomLanguagePrioList used to lookup for classes
        """
        if self._sort_list:
            for i in self.get_sort_list():
                uid = i['uuid']
                for group in (self,) + other_lists:
                    for fac in group:
                        if isinstance(fac, partial):
                            if fac.func.uuid() == uid:
                                return fac
                        else:
                            if fac.uuid() == uid:
                                return fac
        else:
            tmp = []
            for group in (self,) + other_lists:
                for i in group:
                    tmp.append(i)
            tmp.sort(key=self._keyfnc)
            if len(tmp):
                return tmp[0]
            return None

    def get_joined_list(self, other_lists=()):
        """
        Returns a list of the enabled elements.
        
        This is a list of all elements responsible until the Noop Element
        
        @other_lists: other CustomLanguagePrioList used to lookup for classes
        """
        rv = []
        if self._sort_list:
            for i in self.get_sort_list():
                uid = i['uuid']
                for group in (self,) + other_lists:
                    for fac in group:
                        if isinstance(fac, partial):
                            if fac.func.uuid() == uid:
                                if getattr(fac.func, 'IS_DISABELING', False):
                                    break
                                rv.append(fac)
                        else:
                            if fac.uuid() == uid:
                                if getattr(fac, 'IS_DISABELING', False):
                                    break
                                rv.append(fac)
        else:
            for group in (self,) + other_lists:
                for fac in group:
                    if isinstance(fac, partial):
                        if getattr(fac.func, 'IS_DISABELING', False):
                            break
                        rv.append(fac)
                    else:
                        if getattr(fac, 'IS_DISABELING', False):
                            break
                        rv.append(fac)
        return rv

class CustomLanguageMapping(dict):
    """
    this maps language features.
    Sorts it's members after their priority member but allows
    custom order and gets saved in a config file.
    """
    def __init__(self, svc):
        self.svc = svc
        super(CustomLanguageMapping, self).__init__()

    def get_or_create(self, language):
        if language not in self:
            #XXX: some things expect a list ?!
            self[language] = CustomLanguagePrioList()
        return self[language]

    def add(self, language, instance):
        if language and self.svc.doctypes.has_key(language):
            self.svc.doctypes[language].inc_support()
        self.get_or_create(language)
        #self[language].append(instance)

        #def get_prio(elem):
        #    if hasattr(elem, 'priority'):
        #        return elem.priority

        #self[language].sort(key=get_prio, reverse=True)
        if instance not in self[language]:
            self[language].add(instance)

    def remove(self, language, instance):
        if language and self.svc.doctypes.has_key(language):
            self.svc.doctypes[language].dec_support()

        self[language].remove(instance)

    def load(self, data):
        """
        Loads the priority data into the internal structure
        """
        if not isinstance(data, dict):
            logger(_("can't load data structure of type %s") %type(data))
            return
        for key, pluglist in data.iteritems():
            if not self.has_key(key):
                self[key] = CustomLanguagePrioList()
            self[key].set_sort_list(pluglist)
            self[key].customized = True

    def dump(self):
        """
        Dump the mapping to be loaded again.
        """
        rv = {}
        for key, value in self.iteritems():
            if value.customized:
                rv[key] = [{"uuid": x.uuid,
                            "name": x.name,
                            "plugin": x.plugin,
                            "description": x.description} 
                                for x in value.get_full_list()]
        return rv

    def get_best(self, language):
        """
        Returns the best factory for the language
        """
        if self.has_key(language) and language:
            return self[language].get_joined(
                                    other_lists=(self.get_or_create(None),))
        else:
            return self.get_or_create(None).get_joined()

    def get_enabled_list(self, language):
        if self.has_key(language) and language:
            return self[language].get_joined_list(
                                    other_lists=(self.get_or_create(None),))
        else:
            return self.get_or_create(None).get_joined_list()

#FIXME: filtering is currently done very dirty but
# setting a filter function on the model causes segfault
# on windows and performance is non critical here



class LanguageActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'language_type',
            TYPE_MENUTOOL,
            _('_Type'),
            _('Select Document Type'),
            'package_utilities',
            self.on_type_change,
        )

        self.create_action(
            'show_all_types',
            TYPE_REMEMBER_TOGGLE,
            _('Show All Types'),
            _('Show all available types'),
            '',
        )

        self.create_action(
            'language_type_menu',
            TYPE_NORMAL,
            _('_Type'),
            _('Select document type'),
            gtk.STOCK_EXECUTE,
            self.on_type_menu,
        )

        ValidatorConfig.action = self.create_action(
            'show_validator',
            TYPE_REMEMBER_TOGGLE,
            _('_Validator'),
            _('Show the language validator'),
            'error',
            self.on_show_validator,
        )

        OutlinerConfig.action = self.create_action(
            'show_outliner',
            TYPE_REMEMBER_TOGGLE,
            _('_Outliner'),
            _('Show the language browser'),
            'info',
            self.on_show_browser,
        )

        self.create_action(
            'goto_definition',
            TYPE_NORMAL,
            _('Goto _Definition'),
            _('Goto the definition of current word'),
            'goto',
            self.on_goto_definition,
            '<Control>F5'
        )
        self.create_action(
            'show_documentation',
            TYPE_NORMAL,
            _('Show Documentation'),
            _('Show the documentation of cursor position'),
            'help',
            self.on_documentation,
            '<Control>F1'
        )
        self.create_action(
            'language_refresh',
            TYPE_NORMAL,
            _('Refresh'),
            _('Refresh all caches'),
            gtk.STOCK_REFRESH,
            self.on_refresh,
            ''
        )
        self.create_action(
            'focus_outline_browser',
            TYPE_NORMAL,
            _('Focus outline filter'),
            _('Show outline browser and focus filter entry'),
            '',
            self.on_focus_outline,
            '',
            global_=True
        )
        self.create_action(
            'show_language_prio',
            TYPE_TOGGLE,
            _('_Plugin Priorities'),
            _('Configure priorities for language plugins'),
            'info',
            self.on_show_language_prio,
        )


    def on_type_change(self, action):
        pass

    def on_type_menu(self, action):
        menuitem = action.get_proxies()[0]
        menuitem.remove_submenu()
        menuitem.set_submenu(self.svc.create_menu())

    def on_show_validator(self, action):
        if action.get_active():
            self.svc.show_validator()
        else:
            self.svc.hide_validator()

    def on_show_browser(self, action):
        if action.get_active():
            self.svc.show_browser()
        else:
            self.svc.hide_browser()

    def on_goto_definition(self, action):
        self.svc.goto_defintion()

    def on_documentation(self, action):
        self.svc.show_documentation()

    def on_refresh(self, action):
        self.svc.emit('refresh')

    def on_focus_outline(self, action):
        self.get_action('show_outliner').set_active(True)
        self.svc.boss.cmd('window', 'present_view',
                          view=self.svc._view_outliner)
        self.svc._view_outliner.filter_name.select_region(0, -1)
        self.svc._view_outliner.filter_name.grab_focus()

    def on_show_language_prio(self, action):
        self.svc.show_language_prio(action.get_active())


class LanguageCommandsConfig(CommandsConfig):

    # Are either of these commands necessary?

    def get_current_filetype(self):
        return self.svc.current_type

    def present_validator_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_validator())

    def present_browser_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_browser())

    def present_language_prio(self):
        self.svc.show_language_prio(True)

    def hide_language_prio(self):
        self.svc.show_language_prio(False)


class LanguageOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'outline_expand_vars',
            _('Expand outline after n chars'),
            int,
            3,
            _('Expand all entries when searching the outliner after n chars'))

class ValidatorConfig(WindowConfig):
    key = ValidatorView.key
    label_text = ValidatorView.label_text
    description = _("Window that shows validation errors")

class OutlinerConfig(WindowConfig):
    key = BrowserView.key
    label_text = BrowserView.label_text
    description = _("Outliner shows file structure")


class LanguageFeatures(LanguageServiceFeaturesConfig):

    def create(self):
        nmapping = partial(CustomLanguageMapping, self.svc)
        self.publish_special(
            nmapping,
            'info', 'outliner', 'definer',
            'validator', 'completer','documentator',
        )

    def subscribe_all_foreign(self):
        super(LanguageFeatures, self).subscribe_all_foreign()
        self.subscribe_foreign('window', 'window-config',
            OutlinerConfig)
        self.subscribe_foreign('window', 'window-config',
            ValidatorConfig)


class LanguageEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed', 
                                self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-saved', 
                                self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-typchanged', 
                                self.on_document_type)
        self.subscribe_foreign('plugins', 'plugin_started', 
                                self.clear_all_documents)
        self.subscribe_foreign('plugins', 'plugin_stopped', 
                                self.clear_all_documents)


    def create(self):
        self.publish('refresh')
        self.subscribe('refresh', self.on_refresh)

    def on_document_changed(self, document):
        self.svc.on_buffer_changed(document)

    def on_refresh(self):
        self.clear_all_documents()
        self.on_document_changed(
            document=self.svc.boss.get_service('buffer').get_current())

    def clear_all_documents(self, *args, **kwargs):
        for doc in self.svc.boss.get_service('buffer'). \
                    get_documents().itervalues():
            self.svc.clear_document_cache(doc)

    def on_document_type(self, document):
        self.svc.clear_document_cache(document)
        self.svc.on_buffer_changed(document)


class LanguageDbusConfig(DbusConfig):

    @LEXPORT(out_signature = 'as', in_signature = 'ssi')
    def get_completions(self, base, buffer, offset):
        doc = self.svc.boss.cmd('buffer', 'get_current')
        completer = self.svc.get_completer(doc)
        if completer is not None:
            return list(completer.get_completions(base, buffer, offset))
        else:
            return []

    @LEXPORT(out_signature = 'a{s(as)}', in_signature = 's')
    def get_info(self, lang):
        """Returns language info"""
        lst = self.svc.features['info'].get(lang)
        if lst:
            l = lst[0]
            return l.to_dbus()
        return {}

def _get_best(lst, document):
    nlst = list(lst)
    nlst.sort(cmp=lambda x, y: -1*cmp(
         x.func.priorty_for_document(document),
         y.func.priorty_for_document(document))
      )
    return nlst[0]


class Language(LanguageService):
    """ Language manager service """

    actions_config = LanguageActionsConfig
    options_config = LanguageOptionsConfig
    events_config = LanguageEvents
    features_config = LanguageFeatures
    commands_config = LanguageCommandsConfig
    dbus_config = LanguageDbusConfig

    completer_factory = NoopCompleter
    definer_factory = NoopDefiner
    outliner_factory = NoopOutliner
    validator_factory = NoopValidator
    documentator_factory = NoopDocumentator


    def pre_start(self):
        self._language_prio_window = None
        self.doctypes = DOCTYPES
        self._view_outliner = BrowserView(self)
        self._view_validator = ValidatorView(self)
        self.current_type = None
        # add default language info
        self.features.subscribe('info', None, LanguageInfo)

        # we should fill this quite early or the wrong plugins will be used
        # in the beginning
        self.options.register_extra_option("plugin_priorities", {}, 
                            callback=None, workspace=True, notify=True)
        self.load_priority_lists()

    def show_validator(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_validator)

    def hide_validator(self):
        self.boss.cmd('window', 'remove_view', view=self._view_validator)

    def show_browser(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_outliner)

    def hide_browser(self):
        self.boss.cmd('window', 'remove_view', view=self._view_outliner)


    def goto_defintion(self):
        doc = self.boss.cmd('buffer', 'get_current')
        definer = self.get_definer(doc)
        if not definer:
            self.boss.get_service('notify').notify(
            title=_('Goto Definition'),
            data=_('No support for this type found'), timeout=2000)
            return
        res = definer.get_definition(doc.content,
                                     self.boss.editor.get_cursor_position())

        if isinstance(res, Definition):
            self.use_definition(res)
            return
        elif hasattr(res, '__iter__'):
            res = [x for x in res]

        if isinstance(res, (list, tuple)) and len(res) > 1:
            deflist = DefinitionView(self)
            deflist.set_list(res)
            self.boss.cmd('window', 'add_view', paned='Terminal', 
                                                view=deflist)
            gcall(deflist.grab_focus)
        elif res:
            self.use_definition(res[0])
        else:
            self.boss.get_service('notify').notify(
            title=_('Goto Definition'),
            data=_('No definition found'), timeout=2000)


    def use_definition(self, res):
        doc = self.boss.cmd('buffer', 'get_current')
        if res and res.offset is not None:
            if res.file_name == doc.filename:
                self.boss.editor.set_cursor_position(res.offset)
            else:
                self.boss.cmd('buffer', 'open_file', file_name=res.file_name, offset=res.offset)
            gcall(self.boss.editor.grab_focus)
        elif res and res.line is not None:
            if res.file_name == doc.filename:
                self.boss.editor.goto_line(res.line)
            else:
                self.boss.cmd('buffer', 'open_file', file_name=res.file_name, line=res.line)
            gcall(self.boss.editor.grab_focus)

    def show_documentation(self):
        if hasattr(self.boss.editor, 'show_documentation'):
            self.boss.editor.show_documentation()

    def clear_document_cache(self, document):
        for k in ("_lng_outliner", "_lng_validator", "_lng_completer",
                 "_lng_definer", "_lnd_documentator" ,"_lnd_snipper"):
            if hasattr(document, k):
                delattr(document, k)

    def _get_feature(self, document, feature, name, do=None):
        """
        Returns the best feature for a document
        """
        handler = getattr(document, name, None)
        if handler is None:
            type_ = document.doctype
            if type_:
                type_ = type_.internal
            else:
                type_ = None
            factory_list = self.features[feature].get_enabled_list(type_)
            if factory_list:
                # try until one factory has returned a valid result
                for factory in factory_list:
                    handler = factory(document)
                    if handler:
                        setattr(document, name, handler)
                        return handler
        else:
            return handler

    def _get_feature_list(self, document, feature, name, merger, do=None):
        """
        Returns a list of all plugins that provide support and are above
        the disable entry
        """
        handler = getattr(document, name, None)
        if handler is None:
            type_ = document.doctype
            if type_:
                type_ = type_.internal
            else:
                type_ = None
            factory_list = self.features[feature].get_enabled_list(type_)
            if factory_list:
                handler = merger(self, document, factory_list)
                setattr(document, name, handler)
                return handler
        else:
            return handler


    def get_plugins(self, language, feature, default=True):
        """
        Returns a list of registered language plugins for this type
        """
        if isinstance(language, DocType):
            lang = language.internal
        else:
            lang = language
        rv = CustomLanguagePrioList()
        lst = self.features[feature].get(lang)
        if lst:
            rv.extend(lst)
        lst = self.features[feature].get(None)
        if lst:
            rv.extend(lst)
        if not default:
            rv.set_sort_list(self.get_priority_list(language, feature))
        return rv

    def load_priority_lists(self):
        """
        Fill the priority lists by analyzing the options
        """
        for lang, data in \
            self.options.get_extra_value('plugin_priorities').iteritems():
            for type_, lst in data.iteritems():
                self.set_priority_list(lang, type_, lst, save=False)

    def get_priority_list(self, lang, type_):
        """
        Returns the current priority list for a language and type
        """
        opt = self.options.get_extra_value("plugin_priorities")
        if not lang in opt:
            return []
        if not type_ in opt[lang]:
            return []
        return opt[lang][type_]

    def set_priority_list(self, lang, type_, lst, save=True):
        """
        Sets a new priority list on a given language and type_
        
        @lang: internal language name
        @type_: LANGUAGE_PLUGIN_TYPES id
        """
        clist = self.features[type_].get_or_create(lang)
        if hasattr(clist, "set_sort_list"):
            clist.set_sort_list(lst)
        else:
            self.log.warning(_("Try to set a priority list on non priority sublist"))

        # save list in options
        pp = self.options.get_extra_value("plugin_priorities")
        if lst:
            if not pp.has_key(lang):
                pp[lang] = {}
            pp[lang][type_] = lst

        else:
            if not pp.has_key(lang):
                return
            if not pp[lang].has_key(type_):
                return
            del pp[lang][type_]
            if len(pp[lang]) == 0:
                del pp[lang]
        if save:
            self.options.set_extra_value(
                "plugin_priorities",
                self.options.get_extra_value("plugin_priorities"))


    def on_buffer_changed(self, document):
        # wo do nothing if we are not started yet
        if not self.started or not document:
            return
        doctypes = self.doctypes.types_by_filename(document.filename)
        self.current_type = doctypes
        if not doctypes:
            self._view_outliner.clear()
            self._view_validator.clear()
            return

        self._view_outliner.update_filterview(
            self._get_feature(document, 'outliner', '_lng_outliner'))
        self._view_outliner.set_outliner(
            self._get_feature(document, 'outliner', '_lng_outliner'),
            document)
        self._view_validator.set_validator(
            self._get_feature(document, 'validator', '_lng_validator'),
            document)
        self._get_feature_list(document, 'completer', '_lng_completer',
                               MergeCompleter)
        self._get_feature(document, 'definer', '_lng_definer')

    def get_info(self, document):
        return self._get_feature(document, 'info', '_lng_info')

    def get_outliner(self, document):
        return self._get_feature(document, 'outliner', '_lng_outliner')

    def get_validator(self, document):
        return self._get_feature(document, 'validator', '_lng_validator')

    def get_completer(self, document):
        return self._get_feature_list(document, 'completer', '_lng_completer', 
                                      MergeCompleter)

    def get_definer(self, document):
        return self._get_feature(document, 'definer', '_lng_definer')

    def get_documentator(self, document):
        return self._get_feature(document, 'documentator', '_lnd_documentator')

    def get_snippers(self, document):
        handler = getattr(document, '_lnd_snipper', None)
        if not handler:
            type_ = document.doctype
            rv = set()
            if type_:
                rv.update(self.features[(type_.internal, "snipper")])
            rv.update(self.features[(None, "snipper")])
            setattr(document, '_lnd_snipper', rv)
            return rv
        else:
            return handler

    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)

    def show_language_prio(self, visible=True):
        if visible:
            if not self._language_prio_window:
                self._language_prio_window = LanguagePriorityView(self)
            #self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
            self.boss.cmd('window', 'add_detached_view', paned='Plugin',
                view=self._language_prio_window)
        else:
            if self._language_prio_window:
                self.boss.cmd('window', 'remove_view',
                    view=self._language_prio_window)
                self._language_prio_window = None


    def change_doctype(self, widget, current):
        doc = self.boss.cmd('buffer', 'get_current')
        if doc is None:
            return
        doc.doctype = current.get_data('doctype')
        self.boss.get_service('buffer').emit('document-typchanged', document=doc)

    def create_menu(self):
        sections = {}
        doc = self.boss.cmd('buffer', 'get_current')
        menu = gtk.Menu()
        act = None
        a = gtk.RadioAction('None',
                'None',
                'No specific document type',
                gtk.STOCK_NEW,
                0
                )
        a.set_data('doctype', None)
        
        menu.add(a.create_menu_item())
        menu.add(gtk.SeparatorMenuItem())
        show_all = self.get_action('show_all_types').get_active()

        for index, target in enumerate(self.doctypes.itervalues()):
            if not show_all and target.support < 1:
                continue
            act = gtk.RadioAction(target.internal,
                target.human or target.internal,
                target.tooltip,
                '',
                index+1)
            act.set_group(a)
            act.set_data('doctype', target)
            mi = act.create_menu_item()
            if target.section not in sections:
                sections[target.section] = gtk.Menu()
                #menu.add(sections[target.section])
                ms = gtk.MenuItem(target.section)
                ms.set_submenu(sections[target.section])
                menu.add(ms)

            sections[target.section].add(mi)
            if doc and doc.doctype == target:
                a.set_current_value(index+1)
        if doc and not doc.doctype:
            a.set_current_value(0)
        menu.show_all() 
        a.connect('changed', self.change_doctype)

        return menu

Service = Language

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
