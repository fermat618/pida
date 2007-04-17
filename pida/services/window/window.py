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


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE


class WindowCommandsConfig(CommandsConfig):

    def add_view(self, paned, view, present=True):
        self.svc.window.add_view(paned, view, present)

    def add_detached_view(self, paned, view):
        self.add_view(paned, view)
        self.detach_view(view)

    def remove_view(self, view):
        self.svc.window.remove_view(view)

    def detach_view(self, view):
        self.svc.window.detach_view(view)


# Service class
class Window(Service):
    """The PIDA Window Manager"""

    commands_config = WindowCommandsConfig

    def pre_start(self):
        self.window = self.boss.get_window()
        self.gtk_window = self.window.get_toplevel()

    def start(self):
        # Explicitly add the permanent views
        for service in ['project', 'filemanager', 'buffer']:
            view = self.boss.cmd(service, 'get_view')
            self.cmd('add_view', paned='Buffer', view=view, present=False)


# Required Service attribute for service loading
Service = Window



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
