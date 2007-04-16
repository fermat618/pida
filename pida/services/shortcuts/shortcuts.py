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


from kiwi.ui.objectlist import ObjectTree, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView

class ServiceListItem(object):
    
    def __init__(self, svc):
        self._svc = svc
        self.label = svc.get_name().capitalize()
        self.description = svc.__doc__
        

class ShortcutsView(PidaView):

    def create_ui(self):
        self.shortcuts_list = ObjectTree(
            [
                Column('label'),
                Column('value', editable=True),
                Column('doc'),
            ]
        )
        self.add_main_widget(self.shortcuts_list)
        for service in self.svc.boss.get_services():
            sli = ServiceListItem(service)
            self.shortcuts_list.append(None, sli)
            for opt in service.get_keyboard_options().values():
                self.shortcuts_list.append(sli, opt)

        self.shortcuts_list.show_all()

    def decorate_service(self, service):
        return ServiceListItem(service)


class ShortcutsActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_shortcuts',
            TYPE_TOGGLE,
            'Edit Keyboard Shortcuts',
            'Show the PIDA keyboard shortcut editor',
            'key_bindings',
            self.on_show_shortcuts,
            '<Shift><Control>K',
        )

    def on_show_shortcuts(self, action):
        if action.get_active():
            self.svc.show_shortcuts()
        else:
            self.svc.hide_shortcuts()

# Service class
class Shortcuts(Service):
    """Describe your Service Here""" 
    
    actions_config = ShortcutsActionsConfig

    def start(self):
        self._view = ShortcutsView(self)

    def show_shortcuts(self):
        self.boss.add_view('Plugin', self._view)
        self.boss.detach_view(self._view)
        self._view.parent_window.resize(600,400)

    def hide_shortcuts(self):
        self.boss.remove_view(self._view)
        

# Required Service attribute for service loading
Service = Shortcuts



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
