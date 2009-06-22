# -*- coding: utf-8 -*- 
"""
    pida.services.languages
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies support for languages

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL2 or later
"""

import sys
from functools import partial

import gtk
import gobject
import pida.plugins

from kiwi.ui.objectlist import Column
from kiwi.ui.objectlist import ObjectList, COL_MODEL

from outlinefilter import FILTERMAP

from pida.core.environment import plugins_dir, on_windows, get_pixmap_path

from pida.core.doctype import TypeManager
from pida.core.languages import LanguageInfo

from pida.utils.gthreads import GeneratorTask, gcall
from pida.utils.languages import LANG_OUTLINER_TYPES

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE, TYPE_REMEMBER_TOGGLE, TYPE_MENUTOOL, TYPE_NORMAL
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig, EXPORT

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

LEXPORT = EXPORT(suffix='language')

def get_value(tab, key):
    return tab.get(key, None)


class SimpleLanguageMapping(dict):
    """
    this maps language features
    it wont handle priorities 
    """
    def add(self, language, instance):
        if language not in self:
            #XXX: some things expect a list ?!
            self[language] = list()

        self[language].append(instance)

    def remove(self, language, instance):
        self[language].remove(instance)


class PriorityLanguageMapping(dict):
    """
    this maps language features.
    Sorts it's members after their priority member
    """
    def add(self, language, instance):
        if language not in self:
            #XXX: some things expect a list ?!
            self[language] = list()

        self[language].append(instance)

        def get_prio(elem):
            if hasattr(elem, 'priority'):
                return elem.priority

        self[language].sort(key=get_prio, reverse=True)

    def remove(self, language, instance):
        self[language].remove(instance)


class ValidatorView(PidaView):

    key = 'language.validator'

    icon_name = 'python-icon'
    label_text = _('Language Errors')

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

    def on_type_change(self, action):
        pass

    def on_type_menu(self, action):
        menuitem = action.get_proxies()[0]
        #menuitem.remove_submenu()                    # gtk2.12 or higher
        #menuitem.set_submenu(self.svc.create_menu()) # gtk2.12 or higher
        submenu = menuitem.get_submenu()
        for child in submenu.get_children():
            submenu.remove(child)
        submenu_new =   self.svc.create_menu()
        for child in submenu_new.get_children():
            submenu_new.remove(child)
            submenu.append(child)
        
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


class LanguageOptionsConfig(OptionsConfig):
    pass
    def create_options(self):
        self.create_option(
            'outline_expand_vars',
            _('Expand outline after n chars'),
            int,
            3,
            _('Expand all entries when searching the outliner after n chars'))


class LanguageFeatures(FeaturesConfig):

    def create(self):
        self.publish_special(
            PriorityLanguageMapping,
            'info', 'outliner', 'definer',
            'validator', 'completer','documentator',
        )


    def subscribe_all_foreign(self):
        pass


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


class Language(Service):
    """ Language manager service """

    actions_config = LanguageActionsConfig
    options_config = LanguageOptionsConfig
    events_config = LanguageEvents
    features_config = LanguageFeatures
    commands_config = LanguageCommandsConfig
    dbus_config = LanguageDbusConfig

    def pre_start(self):
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
            if type_:
                factories = self.features[feature].get(type_.internal)
            if not factories:
                # get typ unspecific factories
                factories = self.features[feature].get(None)
            if factories:
                #XXX: factoring
                handler = _get_best(factories, document)(document)
                setattr(document, name, handler)
                return handler
        else:
            return handler

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
