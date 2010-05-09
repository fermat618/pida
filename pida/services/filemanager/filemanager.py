# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import pkgutil
import gtk

from os import listdir, path

import os
import shutil
import sys

import cgi

import re

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_DROPDOWNMENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.options import OptionsConfig
from pida.core.environment import on_windows
from pida.core.log import get_logger

from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall
from pida.utils.path import homedir

from pida.ui.views import PidaView, WindowConfig
from pida.ui.objectlist import AttrSortCombo
from pida.ui.dropdownmenutoolbutton import DropDownMenuToolButton
from pida.ui.gtkforms import DialogOptions, create_gtk_dialog
from pygtkhelpers.ui.objectlist import Column, ObjectList

import filehiddencheck

# locale
from pida.core.locale import Locale
locale = Locale('filemanager')
_ = locale.gettext

IEXPORT = EXPORT(suffix='filemanager')

state_text = dict(
        hidden=' ',
        none='?',
        new='A', #XXX
        added='A',
        modified='M',
        ignored=' ',
        normal=' ',
        error='E',
        empty='!',
        conflict='C',
        removed='D',
        missing='!',
        max='+',
        external='>',
        )

state_style = dict( # tuples of (color, is_bold, is_italic)
        unknown=('pida-fm-unknown', False, False),
        hidden=('pida-fm-hidden', False, True),
        ignored=('pida-fm-ignored', False, True),
        #TODO: better handling of normal directories
        clean=('pida-fm-clean', False, False), 
        none=('pida-fm-none', False, True), 
        normal=('pida-fm-normal', False, False),
        error=('pida-fm-error', True, True),
        empty=('pida-fm-empty', False, True),
        modified=('pida-fm-modified', True, False),
        conflict=('pida-fm-conflict', True, True),
        removed=('pida-fm-removed', True, True),
        missing=('pida-fm-missing', True, False),
        new=('pida-fm-new', True, False),
        added=('pida-fm-new', True, False),
        max=('pida-fm-max', False, False),
        external=('pida-fm-external', False, True),
        )


def check_or_home(path):
    if not os.path.isdir(path):
        get_logger('pida.svc.filemanager').info(_("Can't open directory: %s") %path)
        return homedir
    return path

class AlwaysSmall(unicode):
    """
    Helper class to cheat ordering
    """
    def __cmp__(self, other):
        return -1


class FileEntry(object):
    """The model for file entries"""

    def __init__(self, name, parent_path, manager, parent_link=False):
        self._manager = manager
        self.state = 'normal'
        self.parent_link = parent_link
        self.name = name

        if parent_link:
            self.lower_name = AlwaysSmall(self.name.lower())
            self.name = AlwaysSmall(name)
            self.path = parent_path
            self.is_dir = True
            self.is_dir_sort = AlwaysSmall(self.lower_name)
        else:
            self.lower_name = self.name.lower()
            self.name = name
            self.path = os.path.join(parent_path, name)
            self.is_dir = os.path.isdir(self.path)
            self.is_dir_sort = not self.is_dir, self.lower_name

        self.parent_path = parent_path
        self.extension = os.path.splitext(self.name)[-1]
        self.extension_sort = self.extension, self.lower_name
        self.is_dir_sort = not self.is_dir, self.lower_name
        self.visible = False

    @property
    def markup(self):  
        return self.format(cgi.escape(self.name))

    @property
    def icon_stock_id(self):
        if path.isdir(self.path):
            return 'stock_folder'
        else:
            #TODO: get a real mimetype icon
            return 'text-x-generic'

    @property
    def state_markup(self):
        text = state_text.get(self.state, ' ')
        wrap = '<span weight="ultrabold"><tt>%s</tt></span>'
        return wrap%self.format(text)


    def format(self, text):
        color, b, i = state_style.get(self.state, (None, False, False))
        if color:
            color = self._manager.file_list.style.lookup_color(color)
            color = color.to_string()
        else:
            color = "black"
        if b: text = '<b>%s</b>' % text
        if i: text = '<i>%s</i>' % text
        return '<span color="%s">%s</span>' % (color, text)

    def __repr__(self):
        return 'file(%r)' % self.path


class FilemanagerView(PidaView):

    _columns = [
        Column("icon_stock_id", use_stock=True),
        Column("state_markup", use_markup=True),
        Column("markup", use_markup=True),
        Column("lower_name", visible=False, searchable=True),
        ]

    label_text = _('Files')
    icon_name = 'file-manager'
    key = 'filemanager.list'

    def create_ui(self):
        self._vbox = gtk.VBox()
        self._vbox.show()
        self.create_toolbar()
        self._file_hidden_check_actions = {}
        self._create_file_hidden_check_toolbar()
        self.create_file_list()
        self._clipboard_file = None
        self._fix_paste_sensitivity()
        self.add_main_widget(self._vbox)

    def create_file_list(self):
        self.file_list = ObjectList()
        self.file_list.set_headers_visible(False)

        def visible_func(item):
            return item is not None and item.visible
        self.file_list.set_visible_func(visible_func)
        self.file_list.set_columns(self._columns);
        self.file_list.connect('selection-changed', self.on_selection_changed)
        self.file_list.connect('item-activated', self.on_file_activated)
        self.file_list.connect('item-right-clicked', self.on_file_right_click)
        self.entries = {}
        self.update_to_path(self.svc.path)
        self.file_list.show()

        self._file_scroll = gtk.ScrolledWindow(
                hadjustment=self.file_list.props.hadjustment,
                vadjustment=self.file_list.props.vadjustment,
                )
        self._file_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._file_scroll.add(self.file_list)
        self._file_scroll.show()

        self._vbox.pack_start(self._file_scroll)
        self._sort_combo = AttrSortCombo(self.file_list,
            [
                ('is_dir_sort', _('Directories First')),
                ('lower_name', _('File Name')),
                ('name', _('Case Sensitive File Name')),
                ('path', _('File Path')),
                ('extension_sort', _('Extension')),
                ('state', _('Version Control Status')),
            ],
            'is_dir_sort')
        self._sort_combo.show()
        self._vbox.pack_start(self._sort_combo, expand=False)
        self.on_selection_changed(self.file_list)

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_string(
                pkgutil.get_data(
                    __name__,
                    'uidef/filemanager-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_MENU)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()

    def add_or_update_file(self, name, basepath, state, select=False,
                           parent_link=False):
        if basepath != self.path and not parent_link:
            return
        entry = self.entries.setdefault(name,
                                        FileEntry(name, basepath, self,
                                                  parent_link=parent_link))
        entry.state = state

        self.show_or_hide(entry, select=select)

    def show_or_hide(self, entry, select=False):
        def check(checker):
            if (checker.identifier in self._file_hidden_check_actions) and \
               (self._file_hidden_check_actions[checker.identifier].get_active()):
                return checker(name=entry.name, path=entry.parent_path,
                    state=entry.state, )
            else:
                return True

        if self.svc.opt('show_hidden') or entry.parent_link:
            show = True
        else:
            show = all(check(x)
                        for x in self.svc.features['file_hidden_check'])

        entry.visible = show
        if entry not in self.file_list:
            self.file_list.append(entry)
        self.file_list.update(entry)

        if show and select:
            self.file_list.selected_item = entry

    def update_to_path(self, new_path=None, select=None):
        if new_path is None:
            new_path = self.path
        else:
            self.path = check_or_home(new_path)

        self.file_list.clear()
        self.entries.clear()

        if self.svc.opt('show_parent'):
            parent = os.path.normpath(os.path.join(new_path, os.path.pardir))
            # skip if we are already on the root
            if parent != new_path:
                self.add_or_update_file(os.pardir, parent, 
                                        'normal', parent_link=True)

        def work(basepath):
            dir_content = listdir(basepath)
            # add all files from vcs and remove the corresponding items 
            # from dir_content
            for item in self.svc.boss.cmd('versioncontrol', 'list_file_states',
              path=self.path):
                if (item[1] == self.path):
                    try:
                        dir_content.remove(item[0])
                    except:
                        pass
                    yield item
            # handle remaining files
            for filename in dir_content:
                if (path.isdir(path.join(basepath, filename))):
                    state = 'normal'
                else:
                    state = 'unknown'
                yield filename, basepath, state

        # wrap add_or_update_file to set select accordingly
        def _add_or_update_file(name, basepath, state):
            self.add_or_update_file(name, basepath, state, select=(name==select))

        GeneratorTask(work, _add_or_update_file).start(self.path)

        self.create_ancest_tree()

    # This is painful, and will always break
    # So use the following method instead
    def update_single_file(self, name, basepath):
        def _update_file(oname, obasepath, state):
            if oname == name and basepath == obasepath:
                if name not in self.entries:
                    self.entries[oname] = FileEntry(oname, obasepath, self)
                self.entries[oname].state = state
                self.show_or_hide(self.entries[oname])
        for lister in self.svc.features['file_lister']:
            GeneratorTask(lister, _update_file).start(self.path)

    def update_single_file(self, name, basepath, select=False):
        if basepath != self.path:
            return
        if name not in self.entries:
            self.entries[name] = FileEntry(name, basepath, self)
            self.show_or_hide(self.entries[name], select=select)

    def update_removed_file(self, filename):
        entry = self.entries.pop(filename, None)
        if entry is not None and entry.visible:
            self.file_list.remove(entry)

    def create_dir(self, name=None):
        if not name:
            opts = DialogOptions().add('name', label=_("Directory name"), value="")
            create_gtk_dialog(opts, parent=self.svc.boss.window).run()
            name = opts.name
        if name:
            npath = os.path.join(self.path, opts.name)
            if not os.path.exists(npath):
                os.mkdir(npath)
            self.update_single_file(opts.name, self.path, select=True)
             
    def on_file_activated(self, ol, fileentry):
        if os.path.exists(fileentry.path): 
            if fileentry.is_dir: 
                self.svc.browse(fileentry.path)
            else:
                self.svc.boss.cmd('buffer', 'open_file', file_name=fileentry.path)
        else:
            self.update_removed_file(fileentry.name)

    def on_file_right_click(self, ol, item, event=None):
        if item.is_dir: 
            self.svc.boss.cmd('contexts', 'popup_menu', context='dir-menu',
                          dir_name=item.path, event=event, filemanager=True) 
        else:
            self.svc.boss.cmd('contexts', 'popup_menu', context='file-menu',
                          file_name=item.path, event=event, filemanager=True)

    def on_selection_changed(self, ol):
        for act_name in ['toolbar_copy',  'toolbar_delete']:
            self.svc.get_action(act_name).set_sensitive(ol.selected_item is not None)

    def rename_file(self, old, new, entry):
        print 'renaming', old, 'to' ,new

    def create_ancest_tree(self):
        task = AsyncTask(self._get_ancestors, self._show_ancestors)
        task.start(self.path)

    def _on_act_up_ancestor(self, action, directory):
        self.svc.browse(directory)

    def _show_ancestors(self, ancs):
        toolitem = self.svc.get_action('toolbar_up').get_proxies()[0]
        menu = gtk.Menu()
        for anc in ancs:
            action = gtk.Action(anc, anc, anc, 'directory')
            action.connect('activate', self._on_act_up_ancestor, anc)
            menuitem = action.create_menu_item()
            menu.add(menuitem)
        menu.show_all()
        toolitem.set_menu(menu)

    def _get_ancestors(self, directory):
        ancs = [directory]
        parent = None
        while True:
            parent = os.path.dirname(directory)
            if parent == directory:
                break
            ancs.append(parent)
            directory = parent
        return ancs

    def _on_act_file_hidden_check(self, action, check):
        if (check.scope == filehiddencheck.SCOPE_GLOBAL):
            # global
            active_checker = self.svc.opt('file_hidden_check')
            if (action.get_active()):
                active_checker.append(check.identifier)
            else:
                active_checker.remove(check.identifier)
            self.svc.set_opt('file_hidden_check', active_checker)
        else:
            # project
            if (self.svc.current_project is not None):
                section = self.svc.current_project.options.get('file_hidden_check', {})
                section[check.identifier] = action.get_active()
                self.svc.current_project.options['file_hidden_check'] = section
        self.update_to_path()
    
    def __file_hidden_check_scope_project_set_active(self, action):
        """sets active state of a file hidden check action with
           scope = project
           relies on action name = identifier of checker"""
        if (self.svc.current_project is not None):
            section = self.svc.current_project.options.get('file_hidden_check')
            action.set_active(
              (section is not None) and
              (action.get_name() in section) and
              (section[action.get_name()] == 'True'))
        else:
            action.set_active(False)
        
    
    def refresh_file_hidden_check(self):
        """refreshes active status of actions of project scope checker"""
        for checker in self.svc.features['file_hidden_check']:
            if (checker.scope == filehiddencheck.SCOPE_PROJECT):
                action = self._file_hidden_check_actions[checker.identifier]
                self.__file_hidden_check_scope_project_set_active(action)
    
    def _create_file_hidden_check_toolbar(self):
        self._file_hidden_check_actions = {}
        menu = gtk.Menu()
        separator = gtk.SeparatorMenuItem()
        project_scope_count = 0
        menu.append(separator)
        for checker in self.svc.features['file_hidden_check']:
            action = gtk.ToggleAction(checker.identifier, checker.label,
              checker.label, None)
            # active?
            if (checker.scope == filehiddencheck.SCOPE_GLOBAL):
                action.set_active(
                    checker.identifier in self.svc.opt('file_hidden_check'))
            else:
                self.__file_hidden_check_scope_project_set_active(action)

            action.connect('activate', self._on_act_file_hidden_check, checker)
            self._file_hidden_check_actions[checker.identifier] = action
            menuitem = action.create_menu_item()
            if (checker.scope == filehiddencheck.SCOPE_GLOBAL):
                menu.prepend(menuitem)
            else:
                menu.append(menuitem)
                project_scope_count += 1
        menu.show_all()
        if (project_scope_count == 0):
            separator.hide()
        toolitem = None
        for proxy in self.svc.get_action('toolbar_hidden_menu').get_proxies():
            if (isinstance(proxy, DropDownMenuToolButton)):
                toolitem = proxy
                break
        if (toolitem is not None):
            toolitem.set_menu(menu)

    def get_selected_filename(self):
        fileentry = self.file_list.selected_item
        if fileentry is not None:
            return fileentry.path

    def copy_clipboard(self):
        current = self.get_selected_filename()
        if os.path.exists(current):
            self._clipboard_file = current
        else:
            self._clipboard_file = None
        self._fix_paste_sensitivity()

    def _fix_paste_sensitivity(self):
        self.svc.get_action('toolbar_paste').set_sensitive(self._clipboard_file
                                                           is not None)

    def paste_clipboard(self):
        newname = os.path.join(self.path, os.path.basename(self._clipboard_file))
        if newname == self._clipboard_file:
            self.svc.error_dlg(_('Cannot copy files to themselves.'))
            return
        if not os.path.exists(self._clipboard_file):
            self.svc.error_dlg(_('Source file has vanished.'))
            return
        if os.path.exists(newname):
            self.svc.error_dlg(_('Destination already exists.'))
            return
        
        task = AsyncTask(self._paste_clipboard, lambda: None)
        task.start()

    def _paste_clipboard(self):
        #XXX: in thread
        newname = os.path.join(self.path, os.path.basename(self._clipboard_file))
        #XXX: GIO?
        if os.path.isdir(self._clipboard_file):
            shutil.copytree(self._clipboard_file, newname)
        else:
            shutil.copy2(self._clipboard_file, newname)

    def remove_path(self, path):
        task = AsyncTask(self._remove_path, lambda: None)
        task.start(path)

    def _remove_path(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        if path == self._clipboard_file:
            self._clipboard_file = None
            gcall(self._fix_paste_sensitivity)

class FilemanagerEvents(EventsConfig):

    def create(self):
        self.publish(
                'browsed_path_changed',
                'file_renamed')
        
        self.subscribe('file_renamed', self.svc.rename_file)

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
                                     self.svc.on_project_switched)
        self.subscribe_foreign('plugins', 'plugin_started',
            self.on_plugin_started)
        self.subscribe_foreign('plugins', 'plugin_stopped',
            self.on_plugin_stopped);
        self.subscribe_foreign('contexts', 'show-menu',
            self.on_contexts__show_menu)
        self.subscribe_foreign('contexts', 'menu-deactivated',
            self.on_contexts__menu_deactivated)

    def on_plugin_started(self, plugin):
        if (plugin.features.has_foreign('filemanager', 'file_hidden_check')):
            self.svc.refresh_file_hidden_check_menu()
    
    def on_plugin_stopped(self, plugin):
        self.svc.refresh_file_hidden_check_menu()

    def on_contexts__show_menu(self, menu, context, **kw):        
        if 'filemanager' in kw:
            if context == 'file-menu':
                self.svc.get_action('delete-file').set_visible(kw['file_name'] is not None)
            else:
                self.svc.get_action('delete-dir').set_visible(
                    kw['dir_name'] != self.svc.get_view().path)
        else:
            self.svc.get_action('delete-file').set_visible(False)
            self.svc.get_action('delete-dir').set_visible(False)
            self.svc.get_action('browse-for-file').set_visible(
                kw.get('file_name') is not None or
                kw.get('dir_name') is not None)

    def on_contexts__menu_deactivated(self, menu, context, **kw):
        if (kw.has_key('filemanager')):
            if (context == 'file-menu'):
                self.svc.get_action('delete-file').set_visible(False)
            else:
                self.svc.get_action('delete-dir').set_visible(False)


class FilemanagerCommandsConfig(CommandsConfig):
    def browse(self, new_path):
        self.svc.browse(new_path)

    def get_browsed_path(self):
        return self.svc.path

    def get_view(self):
        return self.svc.get_view()

    def present_view(self):
        return self.svc.boss.cmd('window', 'present_view',
            view=self.svc.get_view())

    def update_file(self, filename, dirname):
        if dirname == self.svc.get_view().path:
            self.svc.get_view().update_single_file(filename, dirname)

    def update_removed_file(self, filename, dirname):
        if dirname == self.svc.get_view().path:
            self.svc.get_view().update_removed_file(filename)

    def refresh(self):
        self.svc.get_view().update_to_path()


class FilemanagerWindowConfig(WindowConfig):
    key = FilemanagerView.key
    label_text = FilemanagerView.label_text
    description = _("Filebrowser")

class FilemanagerFeatureConfig(FeaturesConfig):

    def create(self):
        self.publish('file_manager')
        self.publish('file_hidden_check')
        self.subscribe('file_hidden_check', self.dot_files)
        self.subscribe('file_hidden_check', self.regex)

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc, 'filemanager-file-menu.xml'))
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc, 'filemanager-dir-menu.xml'))
        self.subscribe_foreign('window', 'window-config',
                               FilemanagerWindowConfig)

    # File Hidden Checks
    @filehiddencheck.fhc(filehiddencheck.SCOPE_GLOBAL, _("Hide Dot-Files"))
    def dot_files(self, name, path, state):
        return len(name) and name[0] != '.'

    @filehiddencheck.fhc(filehiddencheck.SCOPE_GLOBAL, 
        _("Hide by User defined Regular Expression"))
    def regex(self, name, path, state):
        _re = self.svc.opt('hide_regex')
        if not re:
            return True
        else:
            return re.match(_re, name) is None


class FileManagerOptionsConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
                'show_hidden',
                _('Show hidden files'),
                bool,
                True,
                _('Shows hidden files'),
                workspace=True)

        self.create_option(
                'show_parent',
                _('Show parent entry'),
                bool,
                True,
                _('Shows a ".." entry in the filebrowser'))

        self.create_option(
                'file_hidden_check',
                _('Used file hidden checker'),
                list,
                [],
                _('The used file hidden checker'),
                workspace=True)
        
        self.create_option(
                'last_browsed_remember',
                _('Remember last Path'),
                bool,
                True,
                _('Remembers the last browsed path'))
        
        self.create_option(
                'last_browsed',
                _('Last browsed Path'),
                str,
                path.expanduser('~'),
                _('The last browsed path'),
                safe=False,
                workspace=True)
        
        self.create_option(
                'hide_regex',
                _('Hide regex'),
                str,
                '^\.|.*~|.*\.py[co]$',
                _('Hides files that match the regex'))

class FilemanagerDbusConfig(DbusConfig):
    @IEXPORT(in_signature="s")
    def browse(self, path):
        self.svc.browse(path)

    @IEXPORT(out_signature="s")
    def get_browsed_path(self):
        return self.svc.path

    @IEXPORT(in_signature="s")
    def create_dir(self, path):
        self.svc.create_dir(path)

    @IEXPORT()
    def go_current_file(self):
        self.svc.go_current_file()

    @IEXPORT()
    def go_up(self):
        self.svc.go_up()

    @IEXPORT()
    def refresh_file_hidden_check_menu(self):
        self.svc.refresh_file_hidden_check_menu()

    @IEXPORT()
    def present_view(self):
        self.svc.commands.present_view()

    @IEXPORT()
    def refresh(self):
        self.svc.commands.refresh()



class FileManagerActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'delete-file',
            TYPE_NORMAL,
            _('Delete File'),
            _('Delete selected file'),
            gtk.STOCK_DELETE,
            self.on_delete
        )

        self.create_action(
            'browse-for-file',
            TYPE_NORMAL,
            _('Browse the file directory'),
            _('Browse the parent directory of this file'),
            'file-manager',
            self.on_browse_for_file,
        )

        self.create_action(
            'delete-dir',
            TYPE_NORMAL,
            _('Delete Directory'),
            _('Delete selected directory'),
            gtk.STOCK_DELETE,
            self.on_delete
        )

        self.create_action(
            'browse-for-dir',
            TYPE_NORMAL,
            _('Browse the directory'),
            _('Browse the directory'),
            'file-manager',
            self.on_browse_for_dir,
        )

        self.create_action(
            'show_filebrowser',
            TYPE_NORMAL,
            _('Show _file browser'),
            _('Show the file browser view'),
            'file-manager',
            self.on_show_filebrowser,
            '<Shift><Control>f',
            global_=True
        )

        self.create_action(
            'toolbar_up',
            TYPE_MENUTOOL,
            _('Go Up'),
            _('Go to the parent directory'),
            gtk.STOCK_GO_UP,
            self.on_toolbar_up,
            '<Shift><Control>Up',
        )

        self.create_action(
            'toolbar_terminal',
            TYPE_NORMAL,
            _('Open Terminal'),
            _('Open a terminal in this directory'),
            'terminal',
            self.on_toolbar_terminal,
        )

        self.create_action(
            'toolbar_refresh',
            TYPE_NORMAL,
            _('Refresh Directory'),
            _('Refresh the current directory'),
            gtk.STOCK_REFRESH,
            self.on_toolbar_refresh,
        )

        self.create_action(
            'toolbar_search',
            TYPE_NORMAL,
            _('Find in directory'),
            _('Find in directory'),
            gtk.STOCK_FIND,
            self.on_toolbar_find,
        )


        self.create_action(
            'toolbar_projectroot',
            TYPE_NORMAL,
            _('Project Root'),
            _('Browse the root of the current project'),
            'user-home',
            self.on_toolbar_projectroot,
        )

        self.create_action(
            'toolbar_create_dir',
            TYPE_NORMAL,
            _('Create Directory'),
            _('Create a new directory'),
            gtk.STOCK_DIRECTORY,
            self.on_toolbar_create_dir,
        )

        self.create_action(
            'toolbar_home',
            TYPE_NORMAL,
            _('Home'),
            _('Browse your home directory'),
            'user-home',
            self.on_toolbar_home,
        )

        self.create_action(
            'toolbar_current_file',
            TYPE_NORMAL,
            _('Current Directory'),
            _('Browse directory of current file'),
            gtk.STOCK_GOTO_FIRST,
            self.on_toolbar_current_file,
        )


        self.create_action(
            'toolbar_copy',
            TYPE_NORMAL,
            _('Copy File'),
            _('Copy selected file to the clipboard'),
            gtk.STOCK_COPY,
            self.on_toolbar_copy,
        )

        self.create_action(
            'toolbar_paste',
            TYPE_NORMAL,
            _('Paste File'),
            _('Paste selected file from the clipboard'),
            gtk.STOCK_PASTE,
            self.on_toolbar_paste,
        )

        self.create_action(
            'toolbar_delete',
            TYPE_NORMAL,
            _('Delete File'),
            _('Delete the selected file'),
            gtk.STOCK_DELETE,
            self.on_delete,
        )
        self.create_action(
            'toolbar_toggle_hidden',
            TYPE_TOGGLE,
            _('Show Hidden Files'),
            _('Show hidden files'),
            gtk.STOCK_SELECT_ALL,
            self.on_toggle_hidden,
        )
        self.create_action(
            'toolbar_hidden_menu',
            TYPE_DROPDOWNMENUTOOL,
            None,
            _('Setup which kind of files should be hidden'),
            None,
            None,
        )


    def on_toolbar_find(self, action):
        self.svc.boss.get_service('grepper').show_grepper(self.svc.path)

    def on_browse_for_file(self, action):
        new_path = path.dirname(action.contexts_kw['file_name'])
        self.svc.cmd('browse', new_path=new_path)
        self.svc.cmd('present_view')


    def on_browse_for_dir(self, action):
        new_path = action.contexts_kw['dir_name']
        self.svc.cmd('browse', new_path=new_path)
        self.svc.cmd('present_view')

    def on_show_filebrowser(self, action):
        self.svc.cmd('present_view')

    def on_toolbar_create_dir(self, action):
        self.svc.create_dir()

    def on_toolbar_up(self, action):
        self.svc.go_up()

    def on_toolbar_home(self, action):
        self.svc.cmd('browse', new_path=homedir)
    
    def on_toolbar_current_file(self, action):
        self.svc.go_current_file()

    def on_toolbar_terminal(self, action):
        self.svc.boss.cmd('commander','execute_shell', cwd=self.svc.path)

    def _on_menu_down(self, menu, action):
        action.set_active(False)
        print "down"
    
    def on_toggle_hidden(self, action):
        self.svc.set_opt('show_hidden', action.get_active())
        self.on_toolbar_refresh(action)

    def on_toolbar_refresh(self, action):
        self.svc.get_view().update_to_path()

    def on_toolbar_projectroot(self, action):
        self.svc.browse(self.svc.current_project.source_directory)

    def on_toolbar_copy(self, action):
        self.svc.get_view().copy_clipboard()

    def on_toolbar_paste(self, action):
        self.svc.get_view().paste_clipboard()

    def on_delete(self, action):
        current = self.svc.get_view().get_selected_filename()
        if current is not None:
            if self.svc.yesno_dlg(
                _('Are you sure you want to delete the selected file: %s?'
                % current)
            ):
                self.svc.get_view().remove_path(current)

                if not self.svc.boss.get_service('filewatcher').started:
                    self.svc.get_view().update_to_path()



# Service class
class Filemanager(Service):
    """the Filemanager service"""

    options_config = FileManagerOptionsConfig
    features_config = FilemanagerFeatureConfig
    events_config = FilemanagerEvents
    commands_config = FilemanagerCommandsConfig
    actions_config = FileManagerActionsConfig
    #XXX: disabled
    #dbus_config = FilemanagerDbusConfig

    def pre_start(self):
        self.path = check_or_home(self.opt('last_browsed'))
        self.current_project = None
        self.file_view = FilemanagerView(self)


    def start(self):
        self.on_project_switched(self.current_project)
        self.emit('browsed_path_changed', path=self.path)
        self.get_action('toolbar_toggle_hidden').set_active(
                self.opt('show_hidden'))
        # FIXME: WTF WTF WTF WTF is fixing this the empty icons. 
        # I don't get it ! and why the hack is this happening
        for x in self.actions.list_actions():
            for p in x.get_proxies():
                if hasattr(x.props, "stock_id") and \
                   hasattr(p, "set_stock_id") and \
                   x.props.stock_id is not None:
                    p.set_stock_id(x.props.stock_id)

    def get_view(self):
        return self.file_view
   
    def browse(self, new_path, select=None):
        new_path = path.abspath(new_path)

        if new_path == self.path:
            return
        else:
            self.path = new_path
            self.set_opt('last_browsed', new_path)
            self.file_view.update_to_path(new_path, select=select)
        self.emit('browsed_path_changed', path=new_path)

    def create_dir(self, name=None):
        self.file_view.create_dir(name=name)

    def go_current_file(self):
        cd = self.boss.cmd('buffer', 'get_current')
        if cd and not cd.is_new:
            self.browse(cd.directory)

    def go_up(self):
        oldname = path.basename(self.path)
        dir = path.dirname(self.path)
        if not dir:
            dir = "/" #XXX: unportable, what about non-unix
        self.browse(dir, select=oldname)

    def rename_file(self, old, new, basepath):
        pass

    def refresh_file_hidden_check_menu(self):
        self.get_view()._create_file_hidden_check_toolbar()
    
    def on_project_switched(self, project):
        self.current_project = project
        self.get_action('toolbar_projectroot').set_sensitive(project is not None)
        if self.file_view:
            self.file_view.refresh_file_hidden_check()

# Required Service attribute for service loading
Service = Filemanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
