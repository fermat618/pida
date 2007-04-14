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


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView
from kiwi.ui.objectlist import Column, ObjectList

class TestFile(object):
    def __init__(self, name, manager):
        self._name = name
        self._manager = manager

    def get_name(self):
        return self._name

    def set_name(self, new):
        if self._name !=new:
            self._manager.rename_file(self._name, new, self)
            self._name = new
        return self._name

    name = property(get_name, set_name)

class FilemanagerView(PidaView):
    

    label_text = 'File Manager'

    def create_ui(self):
        self.create_toolbar()
        self.create_file_list()
        self.create_statusbar()

    def create_toolbar(self):
        pass

    def create_file_list(self):
        self.file_list = ObjectList()
        self.file_list.set_columns([
            Column("name", editable=True)
            ]);
        #XXX: real files
        for x in range(10):
            self.file_list.append(TestFile("Test%d"%x, self))
        self.file_list.show()
        self.add_main_widget(self.file_list)
       
    def create_statusbar(self):
        pass

    def rename_file(self, old, new, entry):
        print 'renaming', old, 'to' ,new

class FilemanagerEvents(EventsConfig):
    
    def create_events(self):
        self.create_event('browsepath_switched')
        self.create_event('file_renamed')
        self.subscribe_event('file_renamed', self.svc.rename_file)


# Service class
class Filemanager(Service):
    """the Filemanager service"""

    events_config = FilemanagerEvents

    def start(self):
        self.file_view = FilemanagerView(self)
        self.boss._window.add_view('Buffer',self.file_view)

    
    def rename_file(self, old, new, basepath):
        pass



# Required Service attribute for service loading
Service = Filemanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
