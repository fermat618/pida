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
import gobject

from kiwi.ui.objectlist import Column
from kiwi.ui.objectlist import ObjectList, COL_MODEL

from .outlinefilter import FILTERMAP

from pida.core.environment import on_windows, get_pixmap_path

from pida.core.doctype import TypeManager, DocType
from pida.core.languages import LanguageInfo, LANGUAGE_PLUGIN_TYPES

from pida.utils.gthreads import GeneratorTask, gcall
from pida.utils.languages import LANG_OUTLINER_TYPES
from pida.utils.addtypes import PriorityList

# core
#from pida.core.service import Service
from pida.core.languages import LanguageService, LanguageServiceFeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE, TYPE_REMEMBER_TOGGLE, TYPE_MENUTOOL, TYPE_NORMAL
from pida.core.options import OptionsConfig
#from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.log import get_logger

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo
from pida.ui.prioritywindow import Category, Entry, PriorityEditorView

from .disabled import (NoopCompleter, NoopValidator, NoopDefiner, 
                       NoopDocumentator, NoopOutliner)

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

logger = get_logger('service.language')

LEXPORT = EXPORT(suffix='language')

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
        self.set_sort_list([{"uuid": x.uuid(),
                             "name": x.name,
                             "plugin": x.plugin,
                             "description": x.description} 
                                 for x in self])

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
            return tmp[0]

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
                                    return rv
                                rv.append(fac)
                        else:
                            if fac.uuid() == uid:
                                if getattr(fac, 'IS_DISABELING', False):
                                    return rv
                                rv.append(fac)
        #FIXME: not finished..

class CustomLanguageMapping(dict):
    """
    this maps language features.
    Sorts it's members after their priority member but allows
    custom order and gets saved in a config file.
    """
    def get_or_create(self, language):
        if language not in self:
            #XXX: some things expect a list ?!
            self[language] = CustomLanguagePrioList()
        return self[language]

    def add(self, language, instance):
        self.get_or_create(language)
        #self[language].append(instance)

        #def get_prio(elem):
        #    if hasattr(elem, 'priority'):
        #        return elem.priority

        #self[language].sort(key=get_prio, reverse=True)
        if instance not in self[language]:
            self[language].add(instance)

    def remove(self, language, instance):
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
                self[key] = CustomLanguagePrioList(key=getkey)
            self[key].set_sort_list(pluglist)
            self[key].customized = True

    def dump(self):
        """
        Dump the mapping to be loaded again.
        """
        rv = {}
        for key, value in self.iteritems():
            print key, value, value.customized
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
            return self[language].get_joined(other_lists=(self.get_or_create(None),))
        else:
            return self.get_or_create(None).get_joined()


class LanguageEntry(Entry):

    @classmethod
    def from_plugin(cls, plugin):
        return cls(uid=plugin.func.uuid(),
                   display=plugin.func.name,
                   plugin=plugin.func.plugin,
                   description=plugin.func.description)

    def uuid(self):
        return self.uid

class LanguageSubCategory(Category):
    def __init__(self, svc, lang, type_):
        self.svc = svc
        self.lang = lang
        self.type_ = type_
    
    @property
    def display(self):
        return LANGUAGE_PLUGIN_TYPES[self.type_]['name']

    @property
    def display_info(self):
        if self.type_ == 'completer':
            return _('<i>All plugins before the Disabled entry are used</i>')
        return None

    def get_entries(self, default=False):
        #for type_, info in LANGUAGE_PLUGIN.iteritems():
        for i in self.svc.get_plugins(self.lang, self.type_):
            print i
            yield LanguageEntry.from_plugin(i)

    def commit_list(self, lst):
        print "save list", lst
        prio = [{"uuid": x.uuid(),
                 "name": x.display,
                 "plugin": x.plugin,
                 "description": x.description} 
                                for x in lst]
        self.svc.set_priority_list(self.lang, self.type_, prio)

class LanguageCategory(Category):
    def __init__(self, svc, lang):
        self.svc = svc
        self.lang = lang

    @property
    def display(self):
        return self.svc.doctypes[self.lang].human


    def get_subcategories(self):
        for type_, info in LANGUAGE_PLUGIN_TYPES.iteritems():
            #self.svc.get_plugins(self.lang, type_)
            yield LanguageSubCategory(self.svc, self.lang, type_)
    

class LanguageRoot(Category):
    """
    Data root for PriorityEditor
    """
    def __init__(self, svc):
        self.svc = svc

    def get_subcategories(self):
        for internal, doctype in self.svc.doctypes.iteritems():
            yield LanguageCategory(self.svc, internal)
        

class LanguagePriorityView(PriorityEditorView):
    key = 'language.prio'

    icon_name = 'gtk-library'
    label_text = _('Language Priorities')

    def create_ui(self):
        self.root = LanguageRoot(self.svc)
        self.set_category_root(self.root)

    def can_be_closed(self):
        self.svc.get_action('show_language_prio').set_active(False)

    def on_button_ok__clicked(self, action):
        super(LanguagePriorityView, self).on_button_ok__clicked(action)
        self.svc.get_action('show_language_prio').set_active(False)


class ValidatorView(PidaView):

    key = 'language.validator'

    icon_name = 'python-icon'
    label_text = _('Validator')

    def set_validator(self, validator, document):
        # this is quite an act we have to do here because of the many cornercases
        # 1. Jobs once started run through. This is for caching purpuses as a validator
        # is supposed to cache results, somehow.
        # 2. buffers can switch quite often and n background jobs are still 
        # running

        # set the old task job to default priorty again
        old = self.tasks.get(self.document, None)
        if old:
            old.priority = gobject.PRIORITY_DEFAULT_IDLE

        self.document = document
        self.clear_nodes()

        if self.tasks.has_key(document):
            # set the priority of the current validator higher, so it feels 
            # faster on the current view
            self.tasks[document].priorty = gobject.PRIORITY_HIGH_IDLE
            # when restart is set, the set_validator is run again so the 
            # list gets updated from the validator cache. this happens when
            # the buffer switched to another file and back again
            self.restart = True
            self.svc.log.debug(_('Validator task for %s already running'), document)
            return

        self.restart = False

        if validator:

            def wrap_add_node(document, *args):
                # we need this proxy function as a task may be still running in 
                # background and the document already switched
                # this way we still can fill up the cache by letting the task run
                # sometimes args have a lengh of 0 so we have to catch this
                if self.document == document and len(args):
                    self.add_node(args[0])

            def on_complete(document, validator):
                del self.tasks[document]
                # refire the task and hope the cache will just display stuff,
                # elsewise the task is run again
                validator.sync()
                if document == self.document and self.restart:
                    self.set_validator(validator, document)

            radd = partial(wrap_add_node, document)
            rcomp = partial(on_complete, document, validator)


            task = GeneratorTask(validator.get_validations_cached, 
                                 radd,
                                 complete_callback=rcomp,
                                 priority=gobject.PRIORITY_HIGH_IDLE)
            self.tasks[document] = task
            task.start()

    def add_node(self, node):
        if node:
            node.lookup_color = self.errors_ol.style.lookup_color
            self.errors_ol.append(node)

    def create_ui(self):
        self.document = None
        self.tasks = {}
        self.restart = False
        self.errors_ol = ObjectList(
            Column('markup', use_markup=True)
        )
        self.errors_ol.set_headers_visible(False)
        self.errors_ol.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_main_widget(self.errors_ol)
        self.errors_ol.connect('double-click', self._on_errors_double_clicked)
        self.errors_ol.show_all()
        self.sort_combo = AttrSortCombo(
            self.errors_ol,
            [
                ('lineno', _('Line Number')),
                ('message', _('Message')),
                ('type_', _('Type')),
            ],
            'lineno',
        )
        self.sort_combo.show()
        self.add_main_widget(self.sort_combo, expand=False)

    def clear_nodes(self):
        self.errors_ol.clear()

    def _on_errors_double_clicked(self, ol, item):
        self.svc.boss.editor.cmd('goto_line', line=item.lineno)

    def can_be_closed(self):
        self.svc.get_action('show_validator').set_active(False)


class BrowserView(PidaGladeView):

    key = 'language.browser'


    gladefile = 'outline-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Outliner')

    def create_ui(self):
        self.document = None
        self.tasks = {}
        self.restart = False
        self.source_tree.set_columns(
            [
                Column('icon_name', use_stock=True),
                Column('markup', use_markup=True, expand=True),
                Column('type_markup', use_markup=True),
                Column('sort_hack', visible=False),
                Column('line_sort_hack', visible=False),
            ]
        )
        self.source_tree.set_headers_visible(False)
        self.sort_box = AttrSortCombo(
            self.source_tree,
            [
                ('sort_hack', _('Alphabetical by type')),
                ('line_sort_hack', _('Line Number')),
                ('name', _('Name')),
            ],
            'sort_hack'
        )
        self.sort_box.show()
        self.sort_vbox.pack_start(self.sort_box, expand=False)
        self.filter_model = self.source_tree.get_model().filter_new()
        #FIXME this causes a total crash on win32
        if not on_windows:
            self.source_tree.get_treeview().set_model(self.filter_model)
        self.filter_model.set_visible_func(self._visible_func)
        self.source_tree.get_treeview().connect('key-press-event',
            self.on_treeview_key_pressed)
        self.source_tree.get_treeview().connect('row-activated',
                                     self.do_treeview__row_activated)

        self._last_expanded = None

    def _visible_func(self, model, iter_):
        node = model[iter_][0]
        # FIXME: None objects shouldn't be here, but why ????
        if not node:
            return False
        ftext = self.filter_name.get_text().lower()
        #riter = model.convert_child_iter_to_iter(iter)
        # name filter
        def if_type(inode):
            # type filter
            if inode.filter_type in self.filter_map:
                if self.filter_map[inode.filter_type]:
                    return True
                else:
                    return False
            else:
                return True


        if ftext:
            # we have to test if any children of the current node may match
            def any_child(parent):
                if not parent:
                    return False
                for i in xrange(model.iter_n_children(parent)):
                    child = model.iter_nth_child(parent, i)
                    cnode = model[child][0]
                    if cnode and cnode.name.lower().find(ftext) != -1 and if_type(cnode):
                        return True
                    if model.iter_has_child(child) and any_child(child):
                        return True
                return False

            if (node.name and node.name.lower().find(ftext) != -1) or \
                (model.iter_has_child(iter_) and any_child(iter_)):
                return if_type(node)
            
            return False
        
        return if_type(node)

    def set_outliner(self, outliner, document):
        # see comments on set_validator

        old = self.tasks.get(self.document, None)
        if old:
            old.priority = gobject.PRIORITY_DEFAULT_IDLE

        self.document = document
        self.clear_items()

        if self.tasks.has_key(document):
            # set the priority of the current validator higher, so it feels 
            # faster on the current view
            self.tasks[document].priorty = gobject.PRIORITY_HIGH_IDLE
            # when restart is set, the set_validator is run again so the 
            # list gets updated from the validator cache. this happens when
            # the buffer switched to another file and back again
            self.restart = True
            self.svc.log.debug(_('Outliner task for %s already running'), document)
            return

        self.restart = False

        if outliner:
#            if self.task:
#                self.task.stop()
#            self.task = GeneratorTask(outliner.get_outline_cached, self.add_node)
#            self.task.start()


            def wrap_add_node(document, *args):
                # we need this proxy function as a task may be still running in 
                # background and the document already switched
                # this way we still can fill up the cache by letting the task run
                # sometimes args have a lengh of 0 so we have to catch this
                if self.document == document and len(args):
                    self.add_node(*args)

            def on_complete(document, outliner):
                del self.tasks[document]
                outliner.sync()
                # refire the task and hope the cache will just display stuff,
                # elsewise the task is run again
                if document == self.document and self.restart:
                    self.set_outliner(outliner, document)


            radd = partial(wrap_add_node, document)
            rcomp = partial(on_complete, document, outliner)

            task = GeneratorTask(outliner.get_outline_cached, 
                                 radd,
                                 complete_callback=rcomp,
                                 priority=gobject.PRIORITY_HIGH_IDLE)
            self.tasks[document] = task
            task.start()


    def clear_items(self):
        self.source_tree.clear()

    def add_node(self, node):
        if not node:
            return
        parent = node.parent
        try:
            self.source_tree.append(parent, node)
        except Exception, e:
            import traceback
            traceback.print_exc()
            print "exc", e
            print "add", parent, node

    def can_be_closed(self):
        self.svc.get_action('show_outliner').set_active(False)

    def do_treeview__row_activated(self, treeview, path, view_column):
        "After activated (double clicked or pressed enter) on a row"
        # we have to use this hand connected version as the kiwi one
        # used the wrong model and not our filtered one :(
        try:
            row = self.filter_model[path]
        except IndexError:
            print 'path %s was not found in model: %s' % (
                path, map(list, self._model))
            return
        item = row[COL_MODEL]
        if item.filename is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=item.filename,
                                                     line=item.linenumber)
            self.svc.boss.editor.cmd('grab_focus')
        elif item.linenumber:
            self.svc.boss.editor.cmd('goto_line', line=item.linenumber)
            self.svc.boss.editor.cmd('grab_focus')
        return True

    def update_filterview(self, outliner):
        if outliner:
            def rmchild(widget):
                self.filter_toolbar.remove(widget)
            self.filter_toolbar.foreach(rmchild)

            self.filter_map = dict(
                [(f, FILTERMAP[f]['default']) for f in outliner.filter_type]
                )
            for f in self.filter_map:
                tool_button = gtk.ToggleToolButton()
                tool_button.set_name(str(f))
                tool_button.set_active(self.filter_map[f])
                #FIXME no tooltip on win32
                if not on_windows:
                    tool_button.set_tooltip_text(FILTERMAP[f]['display'])
                tool_button.connect("toggled", self.on_filter_toggled,outliner)
                im = gtk.Image()
                im.set_from_file(get_pixmap_path(FILTERMAP[f]['icon']))
                tool_button.set_icon_widget(im)
                self.filter_toolbar.insert(tool_button, 0)
        #self.options_vbox.add(self.filter_toolbar)
        self.options_vbox.show_all()

    def on_filter_toggled(self, but, outliner):
        self.filter_map[int(but.get_name())] = not self.filter_map[int(but.get_name())]
        #self.set_outliner(outliner, self.document)
        self.filter_model.refilter()

    def on_filter_name_clear__clicked(self, widget):
        self.filter_name.set_text('')

    def on_filter_name__changed(self, widget):
        if len(widget.get_text()) >= self.svc.opt('outline_expand_vars'):
            for i in self.source_tree:
                self.source_tree.expand(
                    i,
                    open_all=True)
        else:
            for i in self.source_tree:
                self.source_tree.collapse(i)

        self.filter_model.refilter()

    def on_treeview_key_pressed(self, tree, event):
        if event.keyval == gtk.keysyms.space:
            # FIXME: who to do this right ??
            cur = self.source_tree.get_selected()
            if self._last_expanded == cur:
                self._last_expanded = None
                self.source_tree.collapse(
                    cur)
            else:
                self.source_tree.expand(
                    cur, 
                    open_all=False)
                self._last_expanded = cur
            return True

    def on_type_changed(self):
        pass
        
#    def read_options(self):
#        return {}


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
            'language_type_menu',
            TYPE_NORMAL,
            _('_Type'),
            _('Select document type'),
            gtk.STOCK_EXECUTE,
            self.on_type_menu,
        )

        self.create_action(
            'show_validator',
            TYPE_REMEMBER_TOGGLE,
            _('_Validator'),
            _('Show the language validator'),
            'error',
            self.on_show_validator,
        )

        self.create_action(
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
            ''
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


class LanguageFeatures(LanguageServiceFeaturesConfig):

    def create(self):
        self.publish_special(
            CustomLanguageMapping,
            'info', 'outliner', 'definer',
            'validator', 'completer','documentator',
        )



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
        for doc in self.svc.boss.get_service('buffer').get_documents().itervalues():
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
            return completer.get_completions(base, buffer, offset)
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
        self.doctypes = TypeManager()
        import deflang
        self.doctypes._parse_map(deflang.DEFMAPPING)
        self._view_outliner = BrowserView(self)
        self._view_validator = ValidatorView(self)
        self.current_type = None
        # add default language info
        self.features.subscribe('info', None, LanguageInfo)

    def start(self):
        acts = self.boss.get_service('window').actions
        
        acts.register_window(self._view_outliner.key,
                             self._view_outliner.label_text)
        acts.register_window(self._view_validator.key,
                             self._view_validator.label_text)

        #FIXME remove
        self.show_language_prio(True)

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
            data=_('No support found'), timeout=2000)
            return
        res = definer.get_definition(doc.content,
                                     self.boss.editor.get_cursor_position())

        if res and res.offset is not None:
            if res.file_name == doc.filename:
                self.boss.editor.set_cursor_position(res.offset)
            else:
                self.boss.cmd('buffer', 'open_file', file_name=res.file_name, offset=res.offset)
            gcall(self.boss.editor.grab_focus)
        else:
            self.boss.get_service('notify').notify(
            data=_('No definition found'), timeout=2000)

    def show_documentation(self):
        if hasattr(self.boss.editor, 'show_documentation'):
            self.boss.editor.show_documentation()

    def clear_document_cache(self, document):
        for k in ("_lng_outliner", "_lng_validator", "_lng_completer",
                 "_lng_definer", "_lnd_documentator" ,"_lnd_snipper"):
            if hasattr(document, k):
                delattr(document, k)

    def _get_feature(self, document, feature, name, do=None):
        handler = getattr(document, name, None)
        if handler is None:
            type_ = document.doctype
            factories = ()
            #if type_:
            factory = self.features[feature].get_best(type_.internal)
            #if not factories:
            #    # get typ unspecific factories
            #    factories = self.features[feature].get(None)
            if factory:
                #XXX: factoring
                handler = factory(document)
                setattr(document, name, handler)
                return handler
        else:
            return handler

    def get_plugins(self, language, feature):
        """
        Returns a list of registered language plugins for this type
        """
        if isinstance(language, DocType):
            lang = language.internal
        else:
            lang = language
        rv = []
        lst = self.features[feature].get(lang)
        if lst:
            rv.extend(lst)
        lst = self.features[feature].get(None)
        if lst:
            rv.extend(lst)
        return rv

    def set_priority_list(self, lang, type_, lst):
        """
        Sets a new priority list on a given language and type_
        
        @lang: internal language name
        @type_: LANGUAGE_PLUGIN_TYPES id
        """
        clist = self.features[type_].get_or_create(lang)
        if hasattr(clist, "set_sort_list"):
            print "set save list", lst
            clist.set_sort_list(lst)
        else:
            self.log.warning(_("Try to set a priority list on non priority sublist"))

    def on_buffer_changed(self, document):
        # wo do nothing if we are not started yet
        if not self.started:
            return
        doctypes = self.doctypes.types_by_filename(document.filename)
        self.current_type = doctypes
        if not doctypes:
            return

        self._view_outliner.update_filterview(
            self._get_feature(document, 'outliner', '_lng_outliner'))
        self._view_outliner.set_outliner(
            self._get_feature(document, 'outliner', '_lng_outliner'),
            document)
        self._view_validator.set_validator(
            self._get_feature(document, 'validator', '_lng_validator'),
            document)
        self._get_feature(document, 'completer', '_lng_completer')
        self._get_feature(document, 'definer', '_lng_definer')

    def get_info(self, document):
        return self._get_feature(document, 'info', '_lng_info')

    def get_outliner(self, document):
        return self._get_feature(document, 'outliner', '_lng_outliner')

    def get_validator(self, document):
        return self._get_feature(document, 'validator', '_lng_validator')

    def get_completer(self, document):
        return self._get_feature(document, 'completer', '_lng_completer')

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
        doc.doctype = current.get_data('doctype')
        self.boss.get_service('buffer').emit('document-typchanged', document=doc)

    def create_menu(self):
        sections = {}
        doc = self.boss.cmd('buffer', 'get_current')
        menu = gtk.Menu()
        a = gtk.RadioAction('None',
                'None',
                'No specific document type',
                gtk.STOCK_NEW,
                hash(None)
                )
        a.set_data('doctype', None)
        
        menu.add(a.create_menu_item())
        menu.add(gtk.SeparatorMenuItem())

        for target in self.doctypes.itervalues():
            act = gtk.RadioAction(target.internal,
                target.human or target.internal,
                target.tooltip,
                '',
                hash(target))
            act.set_group(a)
            act.set_data('doctype', target)
            mi = act.create_menu_item()
            if not sections.has_key(target.section):
                sections[target.section] = gtk.Menu()
                #menu.add(sections[target.section])
                ms = gtk.MenuItem(target.section)
                ms.set_submenu(sections[target.section])
                menu.add(ms)

            sections[target.section].add(mi)
        if doc:
            if doc.doctype:
                act.set_current_value(hash(doc.doctype))
            elif doc.doctype is None:
                act.set_current_value(hash(None))
        menu.show_all() 
        a.connect('changed', self.change_doctype)

        return menu

Service = Language

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
