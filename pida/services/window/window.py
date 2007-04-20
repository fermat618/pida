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
from pida.core.options import OptionsConfig, OTypeBoolean
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE


class WindowCommandsConfig(CommandsConfig):

    def add_view(self, paned, view, present=True):
        self.svc.window.add_view(paned, view, present)

    def add_detached_view(self, paned, view, size=(500,400)):
        self.add_view(paned, view)
        self.detach_view(view, size)

    def remove_view(self, view):
        self.svc.window.remove_view(view)

    def detach_view(self, view, size):
        self.svc.window.detach_view(view, size)

    def present_view(self, view):
        self.svc.window.present_view(view)

class WindowActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_toolbar',
            TYPE_TOGGLE,
            'Show Toolbar',
            'Toggle the visible state of the toolbar',
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>l',
        )

        self.create_action(
            'show_menubar',
            TYPE_TOGGLE,
            'Show Menubar',
            'Toggle the visible state of the menubar',
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>u',
        )

    def on_show_ui(self, action):
        val = action.get_active()
        self.svc.set_opt(action.get_name(), val)
        getattr(self.svc, action.get_name())(val)


class WindowOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_toolbar',
            'Show the toolbar',
            OTypeBoolean,
            True,
            'Whether the main toolbar will be shown',
            self.on_show_ui,
        )

        self.create_option(
            'show_menubar',
            'Show the menubar',
            OTypeBoolean,
            True,
            'Whether the main menubar will be shown',
            self.on_show_ui,
        )

    def on_show_ui(self, client, id, entry, option):
        self.svc.get_action(option.name).set_active(option.get_value())

# Service class
class Window(Service):
    """The PIDA Window Manager"""

    commands_config = WindowCommandsConfig
    options_config = WindowOptionsConfig
    actions_config = WindowActionsConfig

    def start(self):
        # Explicitly add the permanent views
        for service in ['project', 'filemanager', 'buffer']:
            view = self.boss.cmd(service, 'get_view')
            self.cmd('add_view', paned='Buffer', view=view, present=False)
        self._fix_visibilities()

    def _fix_visibilities(self):
        for name in ['show_toolbar', 'show_menubar']:
            val = self.opt(name)
            self.get_action(name).set_active(val)
            getattr(self, name)(val)

    def show_toolbar(self, visibility):
        self.window.set_toolbar_visibility(visibility)

    def show_menubar(self, visibility):
        self.window.set_menubar_visibility(visibility)



# Required Service attribute for service loading
Service = Window



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
