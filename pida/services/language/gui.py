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
import pkgutil
import os

from pygtkhelpers.ui.objectlist import Column, ObjectList

from .outlinefilter import FILTERMAP

from pida.core.environment import on_windows
from pida.core.languages import LANGUAGE_PLUGIN_TYPES
from pida.core.log import get_logger

from pida.utils.gthreads import GeneratorTask

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo
from pida.ui.prioritywindow import Category, Entry, PriorityEditorView
from pida.core.languages import (PRIO_DEFAULT, PRIO_FOREGROUND, 
                                 PRIO_FOREGROUND_HIGH, PRIO_LOW)

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

logger = get_logger('service.language')

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
        self._customized = None
    
    @property
    def display(self):
        return LANGUAGE_PLUGIN_TYPES[self.type_]['name']

    @property
    def display_info(self):
        if self.type_ == 'completer':
            return _('<i>All plugins before the Disabled entry are used</i>')
        return None
    
    def _get_customized(self):
        if self._customized is None:
            self._customized = len(self.svc.get_priority_list(self.lang, self.type_))
        return self._customized
    
    def _set_customized(self, value):
        self._customized = value
    
    customized = property(_get_customized, _set_customized)

    def get_entries(self, default=False):
        #for type_, info in LANGUAGE_PLUGIN.iteritems():
        for i in self.svc.get_plugins(self.lang, self.type_, default=default):
            yield LanguageEntry.from_plugin(i)

    def has_entries(self):
        # the disable service should always exist,so there should be more 
        # then 1 real entries
        return len(self.svc.get_plugins(self.lang, self.type_)) > 1

    def commit_list(self, lst):
        done = []
        prio = []
        for x in lst:
            if x.uuid() in done:
                continue
            prio.append({"uuid": x.uuid(),
                 "name": x.display,
                 "plugin": x.plugin,
                 "description": x.description})
            done.append(x.uuid())

        self.svc.set_priority_list(self.lang, self.type_, prio, save=False)

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

    def needs_visible(self):
        """
        Returns True if it should be displayed
        """
        for type_, info in LANGUAGE_PLUGIN_TYPES.iteritems():
            #self.svc.get_plugins(self.lang, type_)
            if LanguageSubCategory(self.svc, self.lang, type_).has_entries():
                return True

class LanguageRoot(Category):
    """
    Data root for PriorityEditor
    """
    def __init__(self, svc, prioview):
        self.svc = svc
        self.prioview = prioview

    def get_subcategories(self):
        for internal in self.svc.doctypes.iterkeys():
            entry = LanguageCategory(self.svc, internal)
            if self.prioview.all_languages.get_active():
                yield entry
            elif entry.needs_visible():
                yield entry

class LanguagePriorityView(PriorityEditorView):
    """
    Window which allows the user to configure the priorities of plugins
    """
    key = 'language.prio'

    icon_name = 'gtk-library'
    label_text = _('Language Priorities')

    def create_ui(self):
        self.root = LanguageRoot(self.svc, self)
        self.set_category_root(self.root)

    def can_be_closed(self):
        self.svc.get_action('show_language_prio').set_active(False)

    def on_button_apply__clicked(self, action):
        super(LanguagePriorityView, self).on_button_apply__clicked(action)
        #self.svc.get_action('show_language_prio').set_active(False)
        # update all caches
        self.svc.options.set_extra_value(
            "plugin_priorities",
            self.svc.options.get_extra_value("plugin_priorities"))
        self.svc.emit('refresh')

    def on_button_close__clicked(self, action):
        super(LanguagePriorityView, self).on_button_close__clicked(action)
        self.svc.get_action('show_language_prio').set_active(False)

class ValidatorView(PidaView):

    key = 'language.validator'

    icon_name = 'python-icon'
    label_text = _('Validator')

    def create_ui(self):
        self._last_selected = None
        self.document = None
        self.tasks = {}
        self.restart = False
        self.errors_ol = ObjectList([
            Column('markup', use_markup=True)
        ])
        self.errors_ol.set_headers_visible(False)
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.show()
        self.scrolled_window.add(self.errors_ol)

        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_main_widget(self.scrolled_window)

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

    def set_validator(self, validator, document):
        # this is quite an act we have to do here because of the many cornercases
        # 1. Jobs once started run through. This is for caching purpuses as a validator
        # is supposed to cache results, somehow.
        # 2. buffers can switch quite often and n background jobs are still 
        # running

        # set the old task job to default priorty again
        old = self.tasks.get(self.document, None)
        if old:
            old.priority = PRIO_LOW

        self.document = document
        self.clear()

        if self.tasks.has_key(document):
            # set the priority of the current validator higher, so it feels 
            # faster on the current view
            if self.svc.boss.window.paned.is_visible_pane(self.pane):
                prio = PRIO_FOREGROUND
            else:
                prio = PRIO_DEFAULT
            self.tasks[document].priorty = prio
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
                if self.document == document and args:
                    item = args[0]
                    self.add_node(item)
                    if self._last_selected:
                        if self._last_selected[0] == self.document:
                            if item.lineno == self._last_selected[1]:
                                self.errors_ol.selected_item = item

            def on_complete(document, validator):
                del self.tasks[document]
                # refire the task and hope the cache will just display stuff,
                # elsewise the task is run again
                validator.sync()

                if document == self.document and self.restart:
                    self.set_validator(validator, document)

            radd = partial(wrap_add_node, document)
            rcomp = partial(on_complete, document, validator)

            if self.svc.boss.window.paned.is_visible_pane(self. pane):
                prio = PRIO_FOREGROUND
            else:
                prio = PRIO_DEFAULT

            task = GeneratorTask(validator.get_validations_cached, 
                                 radd,
                                 complete_callback=rcomp,
                                 priority=prio)
            self.tasks[document] = task
            task.start()

    def add_node(self, node):
        if node:
            node.lookup_color = self.errors_ol.style.lookup_color
            self.errors_ol.append(node)


    def clear(self):
        self.errors_ol.clear()

    def on_errors_ol__selection_changed(self, ol):
        item = ol.selected_item # may be None
        self._last_selected = (self.document, getattr(item, 'lineno', 0))

    def on_errors_ol__item_activated(self, ol, item):
        self.svc.boss.editor.cmd('goto_line', line=int(item.lineno))

    def can_be_closed(self):
        self.svc.get_action('show_validator').set_active(False)


class BrowserView(PidaGladeView):
    """
    Window with the outliner
    """

    key = 'language.browser'


    gladefile = 'outline_browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Outliner')

    def create_ui(self):
        self.document = None
        self.tasks = {}
        self.restart = False
        self.source_tree.set_columns([
            Column('icon_name', use_stock=True),
            Column('markup', use_markup=True, expand=True),
            Column('type_markup', use_markup=True),
            Column('sort_hack', visible=False),
            Column('line_sort_hack', visible=False),
        ])
        self.source_tree.set_headers_visible(False)
        # faster lookups on the id property
        self.source_tree_ids = {}

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
        self.filter_model = self.source_tree.model_filter
        #FIXME this causes a total crash on win32
        self.source_tree.set_visible_func(self._visible_func)

        self._last_expanded = None
        self._last_outliner = None

    def _visible_func(self, node):
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
            old.priority = PRIO_DEFAULT

        self.document = document
        self.clear()

        if document in self.tasks:
            # set the priority of the current validator higher, so it feels 
            # faster on the current view
            if self.svc.boss.window.paned.is_visible_pane(self.pane):
                prio = PRIO_FOREGROUND
            else:
                prio = PRIO_DEFAULT
            self.tasks[document].priorty = prio
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
                if self.document == document and args:
                    self.add_node(*args)

            def on_complete(document, outliner):
                del self.tasks[document]
                outliner.sync()
                # fire refilter so the list is updated after buffer changed
                self.filter_model.refilter()
                # refire the task and hope the cache will just display stuff,
                # elsewise the task is run again
                if document == self.document and self.restart:
                    self.set_outliner(outliner, document)


            radd = partial(wrap_add_node, document)
            rcomp = partial(on_complete, document, outliner)

            if self.svc.boss.window.paned.is_visible_pane(self.pane):
                prio = PRIO_FOREGROUND
            else:
                prio = PRIO_DEFAULT

            task = GeneratorTask(outliner.get_outline_cached, 
                                 radd,
                                 complete_callback=rcomp,
                                 priority=prio)
            self.tasks[document] = task
            task.start()


    def clear(self):
        self.source_tree.clear()
        self.source_tree_ids = {}

    def get_by_id(self, id_):
        """
        Return the OutlinerItem by it's id property
        """
        def lookup(model, path, iter):
            if model.get_value(iter, 0).id == id_:
                lookup.rv = model.get_value(iter, 0)
                return True

        self.source_tree.get_model().foreach(lookup)
        return getattr(lookup, 'rv', None)


    def add_node(self, node):
        if not node:
            return

        if node.id:
            self.source_tree_ids[node.id] = node

        if node.parent:
            parent = node.parent
        elif node.parent_id:
            # only the parent_id was submitted so we have to look the parent up
            try:
                parent = self.source_tree_ids[node.parent_id]
            except KeyError:
                # try a deep lookup
                parent = self.get_by_id(node.parent_id)
        else:
            parent = None

        try:
            self.source_tree.append(node, parent=parent)
        except Exception, e:
            import traceback
            traceback.print_exc()
            print "exc", e
            print "add", parent, node

    def can_be_closed(self):
        self.svc.get_action('show_outliner').set_active(False)

    def on_source_tree__item_activated(self, ol, item):
        if item.filename is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=item.filename,
                                                     line=item.linenumber)
            self.svc.boss.editor.cmd('grab_focus')
        elif item.linenumber:
            self.svc.boss.editor.cmd('goto_line', line=item.linenumber)
            self.svc.boss.editor.cmd('grab_focus')

    def update_filterview(self, outliner):
        if ((outliner and not self._last_outliner) or
            (self._last_outliner and self._last_outliner.name != outliner.name)):
            self._last_outliner = outliner
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
                image_name = FILTERMAP[f]['icon']

                #XXX: put into pygtkhelpers?
                image_data = pkgutil.get_data(__name__, 'pixmaps/%s.png'%image_name)
                loader = gtk.gdk.PixbufLoader()
                loader.write(image_data)
                loader.close()

                im = gtk.Image()
                im.set_from_pixbuf(loader.get_pixbuf())
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

    def on_source_tree__key_press_event(self, tree, event):
        if event.keyval == gtk.keysyms.space:
            # FIXME: how to do this right ??
            cur = self.source_tree.selected_item
            if self._last_expanded == cur:
                self._last_expanded = None
                self.source_tree.collapse_item(cur)
            else:
                self.source_tree.expand_item(cur, open_all=False)
                self._last_expanded = cur
            return True

    def on_type_changed(self):
        pass

#    def read_options(self):
#        return {}

class DefinitionView(PidaGladeView):
    """
    List of Definitions if language plugin returns more then one result
    """

    key = 'language.definition'

    gladefile = 'definition'
    #icon_name = 'python-icon'
    label_text = _('Definition')


    def create_ui(self):
        self._project = None
        self.list.set_columns([
            Column('icon_name', title=' ', width=35, use_stock=True, expand=False),
            Column('signature', data_type=str, title=_('Symbol'),
                    format_func=self.format_signature,
                    expander=True, searchable=True),
            Column('file_name', data_type=str, title=_('Filename'),
                    format_func=self.format_path,
                    expander=True, searchable=True),
            Column('line', data_type=int, title=_('Line'))
        ])

    def grab_focus(self):
        self.list.grab_focus()
        if len(self.list):
            self.list.selectected_item = self.list[0]
            #XXX: scroll to it ? scroll=True)

    def format_signature(self, value):
        if value:
            return value[:80]
        return ''

    def format_path(self, path):
        #XXX: should look up for all projects
        #XXX: _project is broken
        if not self._project:
            return path
        comps = self._project.get_relative_path_for(path)
        if comps:
            return os.path.sep.join(comps)
        return path

    def set_list(self, lst):
        #XXX: _project is broken
        self._project = self.svc.boss.cmd('project', 'get_current_project')
        self.list.clear()
        for i in lst:
            self.list.append(i)

    def on_list__row_activated(self, widget, row):
        self.svc.use_definition(row)

    def on_list__double_click(self, widget, row):
        self.svc.use_definition(row)

