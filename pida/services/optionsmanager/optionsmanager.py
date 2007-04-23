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

from pida.ui.views import PidaGladeView


class PidaOptionsView(PidaGladeView):

    gladefile = 'options-editor'


class OptionsActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_options',
            TYPE_TOGGLE,
            'Edit Preferences',
            'Edit the PIDA preferences',
            'properties',
            self.on_show_options,
            '<Shift><Control>#'
        )

    def on_show_options(self, action):
        if action.get_active():
            self.svc.show_options()
        else:
            self.svc.hide_options()

# Service class
class Optionsmanager(Service):
    """Describe your Service Here""" 

    actions_config = OptionsActions

    def pre_start(self):
        self._view = PidaOptionsView(self)

    def show_options(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_options(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

# Required Service attribute for service loading
Service = Optionsmanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
