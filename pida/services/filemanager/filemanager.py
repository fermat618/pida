# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


from weakref import proxy
import gtk

from os import listdir, path

import os

import cgi

import re

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.options import OptionsConfig, OTypeBoolean, OTypeString
from pida.core.environment import get_uidef_path

from pida.utils.gthreads import GeneratorTask, AsyncTask

from pida.ui.views import PidaView
from pida.ui.objectlist import AttrSortCombo
from kiwi.ui.objectlist import Column, ColoredColumn, ObjectList

# locale
from pida.core.locale import Locale
locale = Locale('filemanager')
_ = locale.gettext


state_text = dict(
        hidden=' ',
        none='?',
        new='A',
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
        hidden=('lightgrey', False, True),
        ignored=('lightgrey', False, True),
        #TODO: better handling of normal directories
        none=('#888888', False, True), 
        normal=('black', False, False),
        error=('darkred', True, True),
        empty=('black', False, True),
        modified=('darkred', True, False),
        conflict=('dargred', True, True),
        removed=('#c06060', True, True),
        missing=('#00c0c0', True, False),
        new=('blue', True, False),
        max=('#c0c000', False, False),
        external=('#333333', False, True),
        )


class FileEntry(object):
    """The model for file entries"""

    def __init__(self, name, parent_path, manager):
        self._manager = manager
        self.state = 'normal'
        self.name = name
        self.lower_name = self.name.lower()
        self.parent_path = parent_path
        self.path = os.path.join(parent_path, name)
        self.extension = os.path.splitext(self.name)[-1]
        self.extension_sort = self.extension, self.lower_name
        self.is_dir = os.path.isdir(self.path)
        self.is_dir_sort = not self.is_dir, self.lower_name
        self.icon_stock_id = self.get_icon_stock_id()
        self.visible = False

    def get_markup(self):
        return self.format(cgi.escape(self.name))

    markup = property(get_markup)

    def get_icon_stock_id(self):
        if path.isdir(self.path):
            return 'stock_folder'
        else:
            #TODO: get a real mimetype icon
            return 'text-x-generic'

    def get_state_markup(self):
        text = state_text.get(self.state, ' ')
        wrap = '<span weight="ultrabold"><tt>%s</tt></span>'
        return wrap%self.format(text)

    state_markup = property(get_state_markup)
        
    def format(self, text):
        color, b, i = state_style.get(self.state, ('black', False, False))
        if b:
            text = '<b>%s</b>' % text
        if i:
            text = '<i>%s</i>' % text
        return '<span color="%s">%s</span>' % (color, text)


class FilemanagerView(PidaView):

    _columns = [
        Column("icon_stock_id", use_stock=True),
        Column("state_markup", use_markup=True),
        Column("markup", use_markup=True),
        Column("lower_name", visible=False, searchable=True),
        ]

    label_text = _('Files')
    icon_name = 'file-manager'

    def create_ui(self):
        self._vbox = gtk.VBox()
        self._vbox.show()
        self.create_toolbar()
        self.create_ancestors()
        self.create_file_list()
        self.create_statusbar()
        self.add_main_widget(self._vbox)

    def create_statusbar(self):
        pass

    def create_ancestors(self):
        pass

    def create_file_list(self):
        self.file_list = ObjectList()
        self.file_list.set_headers_visible(False)
        self.file_list.set_columns(self._columns);
        self.file_list.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        #XXX: real file
        self.file_list.connect('row-activated', self.on_file_activated)
        self.file_list.connect('right-click', self.on_file_right_click)
        self.entries = {}
        self.update_to_path(self.svc.path)
        self.file_list.show()
        self._vbox.pack_start(self.file_list)
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

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_file(get_uidef_path('filemanager-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_MENU)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()


    def add_or_update_file(self, name, basepath, state):
        if basepath != self.path:
            return
        entry = self.entries.setdefault(name, FileEntry(name, basepath, self))
        entry.state = state

        self.show_or_hide(entry)

    def show_or_hide(self, entry):
        from operator import and_
        def check(checker):
            return checker(
                    name=entry.name, 
                    path=entry.parent_path,
                    state=entry.state,
                    )
        show = reduce(and_, map(check, self.svc.features("file_hidden_check")))
        if show:
            if entry.visible:
                self.file_list.update(entry)
            else:
                self.file_list.append(entry)
                entry.visible = True
        else:
            if entry.visible:
                self.file_list.remove(entry)
                entry.visible = False

    def update_to_path(self, new_path=None):
        if new_path is None:
            new_path = self.path
        else:
            self.path = new_path

        self.file_list.clear()
        self.entries.clear()

        for lister in self.svc.features("file_lister"):
            GeneratorTask(lister, self.add_or_update_file).start(self.path)

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
        for lister in self.svc.features("file_lister"):
            GeneratorTask(lister, _update_file).start(self.path)

    def update_single_file(self, name, basepath):
        if basepath != self.path:
            return
        if name not in self.entries:
            self.entries[name] = FileEntry(name, basepath, self)
            self.show_or_hide(self.entries[name])

    def update_removed_file(self, filename):
        entry = self.entries.pop(filename, None)
        if entry is not None and entry.visible:
            self.file_list.remove(entry)

    def on_file_activated(self, rowitem, fileentry):
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
                          dir_name=item.path, event=event) 
        else:
            self.svc.boss.cmd('contexts', 'popup_menu', context='file-menu',
                          file_name=item.path, event=event) 

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
        while directory != '/':
            parent = os.path.dirname(directory)
            ancs.append(parent)
            directory = parent
        return ancs
            


class FilemanagerEvents(EventsConfig):

    def create_events(self):
        self.create_event('browsed_path_changed')
        self.create_event('file_renamed')
    
    def subscribe_foreign_events(self):    
        self.subscribe_event('file_renamed', self.svc.rename_file)
        self.subscribe_foreign_event('project', 'project_switched',
                                     self.svc.on_project_switched)

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
        


class FilemanagerFeatureConfig(FeaturesConfig):

    def create_features(self):
        self.create_feature("file_manager")
        self.create_feature("file_hidden_check")
        self.create_feature("file_lister")

    def subscribe_foreign_features(self):
        self.subscribe_feature("file_hidden_check", self.svc.check_hidden_regex)
        self.subscribe_feature("file_lister", self.svc.file_lister)
        
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'filemanager-file-menu.xml'))
        self.subscribe_foreign_feature('contexts', 'dir-menu',
            (self.svc.get_action_group(), 'filemanager-dir-menu.xml'))



class FileManagerOptionsConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
                'show_hidden',
                _('Show hidden files'),
                OTypeBoolean,
                True,
                _('Shows hidden files'))
        
        self.create_option(
                'last_browsed_remember',
                _('Remember last Path'),
                OTypeBoolean,
                True,
                _('Remembers the last browsed path'))
        
        self.create_option(
                'last_browsed',
                _('Last browsed Path'),
                OTypeString,
                path.expanduser('~'),
                _('The last browsed path'))
        
        self.create_option(
                'hide_regex',
                _('Hide regex'),
                OTypeString,
                '^\.|.*\.py[co]$',
                _('Hides files that match the regex'))

class FileManagerActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'browse-for-file',
            TYPE_NORMAL,
            _('Browse the file directory'),
            _('Browse the parent directory of this file'),
            'file-manager',
            self.on_browse_for_file,
            'NOACCEL',
        )

        self.create_action(
            'browse-for-dir',
            TYPE_NORMAL,
            _('Browse the directory'),
            _('Browse the directory'),
            'file-manager',
            self.on_browse_for_dir,
            'NOACCEL',
        )

        self.create_action(
            'show_filebrowser',
            TYPE_NORMAL,
            _('Show file browser'),
            _('Show the file browser view'),
            'file-manager',
            self.on_show_filebrowser,
            '<Shift><Control>f'
        )

        self.create_action(
            'toolbar_up',
            TYPE_MENUTOOL,
            _('Go Up'),
            _('Go to the parent directory'),
            gtk.STOCK_GO_UP,
            self.on_toolbar_up,
            'NOACCEL',
        )

        self.create_action(
            'toolbar_terminal',
            TYPE_NORMAL,
            _('Open Terminal'),
            _('Open a terminal in this directory'),
            'terminal',
            self.on_toolbar_terminal,
            'NOACCEL',
        )

        self.create_action(
            'toolbar_refresh',
            TYPE_NORMAL,
            _('Refresh Directory'),
            _('Refresh the current directory'),
            gtk.STOCK_REFRESH,
            self.on_toolbar_refresh,
            'NOACCEL',
        )

        self.create_action(
            'toolbar_projectroot',
            TYPE_NORMAL,
            _('Project Root'),
            _('Browse the root of the current project'),
            'user-home',
            self.on_toolbar_projectroot,
            'NOACCEL',
        )


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

    def on_toolbar_up(self, action):
        self.svc.go_up()

    def on_toolbar_terminal(self, action):
        self.svc.boss.cmd('commander','execute_shell', cwd=self.svc.path)

    def on_toolbar_refresh(self, action):
        self.svc.get_view().update_to_path()

    def on_toolbar_projectroot(self, action):
        self.svc.browse(self.svc.current_project.source_directory)



# Service class
class Filemanager(Service):
    """the Filemanager service"""

    options_config = FileManagerOptionsConfig
    features_config = FilemanagerFeatureConfig
    events_config = FilemanagerEvents
    commands_config = FilemanagerCommandsConfig
    actions_config = FileManagerActionsConfig

    def pre_start(self):
        self.path = self.opt('last_browsed')

    def start(self):
        self.file_view = FilemanagerView(self)
        self.emit('browsed_path_changed', path=self.path)
        self.on_project_switched(None)

    def get_view(self):
        return self.file_view
   
    def browse(self, new_path):
        new_path = path.abspath(new_path)
        if new_path == self.path:
            return
        else:
            self.path = new_path
            self.set_opt('last_browsed', new_path)
            self.file_view.update_to_path(new_path)
        self.emit('browsed_path_changed', path=new_path)


    def go_up(self):
        dir = path.dirname(self.path)
        if not dir:
            dir = "/" #XXX: unportable, what about non-unix
        self.browse(dir)

    def check_hidden_regex(self, name, path, state):
        _re = self.opt('hide_regex')
        if not re:
            return True
        else:
            return re.match(_re, name) is None

    def file_lister(self, basepath):
        for name in listdir(basepath):
            yield name, basepath, 'normal'

    def rename_file(self, old, new, basepath):
        pass

    def on_project_switched(self, project):
        self.current_project = project
        self.get_action('toolbar_projectroot').set_sensitive(project is not None)



# Required Service attribute for service loading
Service = Filemanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
