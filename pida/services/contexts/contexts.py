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

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.environment import get_uidef_path


CONTEXT_TYPES = [
    'file-menu',
    'dir-menu',
    'url-menu',
]

class ContextFeaturesConfig(FeaturesConfig):

    def create_features(self):
        for context in CONTEXT_TYPES:
            self.create_feature(context)

class ContextCommandsConfig(CommandsConfig):

    def get_menu(self, context, **kw):
        return self.svc.get_menu(context, **kw)

    def popup_menu(self, context, event=None, **kw):
        menu = self.get_menu(context, **kw)
        menu.show_all()
        if event is None:
            button = 3
            time = gtk.get_current_event_time()
        else:
            button = event.button
            time = event.time
        menu.popup(None, None, None, button, time)


# Service class
class Contexts(Service):
    """Describe your Service Here""" 

    features_config = ContextFeaturesConfig
    commands_config = ContextCommandsConfig

    def start(self):
        self._create_uims()

    def _create_uims(self):
        self._uims = {}
        for context in CONTEXT_TYPES:
            uim = self._uims[context] = gtk.UIManager()
            uim.add_ui_from_file(self.get_base_ui_definition_path(context))
            for ag, uidef in self.features(context):
                uim.insert_action_group(ag, 0)
                uidef_path = get_uidef_path(uidef)
                uim.add_ui_from_file(uidef_path)

    def get_base_ui_definition_path(self, context):
        file_name = '%s.xml' % context
        return get_uidef_path(file_name)

    def get_menu(self, context, **kw):
        for group in self._uims[context].get_action_groups():
            for action in group.list_actions():
                action.contexts_kw = kw
        menu = self._uims[context].get_toplevels('popup')[0]
        return menu



# Required Service attribute for service loading
Service = Contexts



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
