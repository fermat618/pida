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

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView
from kiwi.ui.objectlist import Column, ColoredColumn, ObjectList

class FileEntry(object):
    """The model for file entries"""

    _state = None
    _icon = None

    def __init__(self, name, path_, manager):
        self._name = name
        self._manager = manager
        self.path = path.join(path_, name)
    
    @property
    def name(self):
        return self._name.replace("&","&amp;")

    @property
    def icon(self):
        if self._icon is not None:
            return self._icon
        elif path.isdir(self.path):
            return 'stock_folder'
        else:
            #TODO: get a real mimetype icon
            return 'text-x-generic'
    
    @property
    def state(self):
        if self._state is None:
            return ""

class FilemanagerView(PidaView):
    
    _columns = [
        Column("icon", use_stock=True),
        Column("state", use_markup=True),
        Column("name", use_markup=True)
        ]

    label_text = 'Files'
    
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
        #XXX: real file
        self.file_list.connect('row-activated', self.act_double_click)
        self.update_to_path(path.expanduser('~'))
        self.file_list.show()
        self._vbox.pack_start(self.file_list)
       
    def create_toolbar(self):
        self._tips = gtk.Tooltips()
        self._toolbar = gtk.Toolbar()
        self._toolbar.set_icon_size(gtk.ICON_SIZE_MENU)
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.show()
        self._vbox.pack_start(self._toolbar, expand=False)
        
        gen_action = self.generate_action_button
            
        self._upact = gen_action(
                'Up', 'Up',
                'Browse the parent directory',
                gtk.STOCK_GO_UP,
                self.act_go_up
                )


        self._newfileact = gen_action(
                'Cmd', 'Terminal',
                'Start a terminal here',
                gtk.STOCK_NEW,
                self.start_term
                )
        
    def add_action_to_toolbar(self, action):
         toolitem = action.create_tool_item()
         self._toolbar.add(toolitem)
         toolitem.set_tooltip(self._tips, action.props.tooltip)
         return toolitem

    #TODO: move to the actionsconfig
    def generate_action_button(self, name, verbose_name, tooltip, icon,
            activate_callback=None):
        act = gtk.Action(name, verbose_name, tooltip, icon)
        toolitem = self.add_action_to_toolbar(act)
        if activate_callback is not None:
            act.connect('activate', activate_callback)
        return act

    def start_term(self, action):
        self.svc.boss.cmd('commander','execute_shell', cwd=self.svc.path)

    def update_to_path(self, new_path=None):
        if new_path is None:
            new_path = self.path
        else:
            self.path = new_path

        files = [FileEntry(name, new_path, self) for name in listdir(new_path)]
        self.file_list.add_list(files, clear=True)
    
    def act_double_click(self, rowitem, fileentry):
        target = path.normpath(
                 path.join(self.path, fileentry.name))
        if path.isdir(target):
            self.svc.browse(target)
        else:
            self.svc.boss.cmd('buffer', 'open_file', file_name=target)

    def act_go_up(self, action):
        self.svc.go_up()

    def rename_file(self, old, new, entry):
        print 'renaming', old, 'to' ,new

class FilemanagerEvents(EventsConfig):
    
    def create_events(self):
        self.create_event('browsepath_switched')
        self.create_event('file_renamed')
    
    def subscribe_events(self):    
        self.subscribe_event('file_renamed', self.svc.rename_file)

class FilemanagerCommandsConfig(CommandsConfig):
    def browse(self, new_path):
        self.svc.browse(new_path)


class FilemanagerFeatureConfig(FeaturesConfig):

    def create_features(self):
        self.create_feature("file-manager")


# Service class
class Filemanager(Service):
    """the Filemanager service"""

    features_config = FilemanagerFeatureConfig
    events_config = FilemanagerEvents

    def start(self):
        self.path = "/"
        self.file_view = FilemanagerView(self)
        self.boss._window.add_view('Buffer',self.file_view)
   
    def browse(self, new_path):
        
        new_path = path.abspath(new_path)
        if new_path == self.path:
            return
        else:
            self.path = new_path
            self.file_view.update_to_path(new_path)

    def go_up(self):
        dir = path.dirname(self.path)
        if not dir:
            dir = "/" #XXX: unportable, what about non-unix
        self.browse(dir)


    def rename_file(self, old, new, basepath):
        pass



# Required Service attribute for service loading
Service = Filemanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
