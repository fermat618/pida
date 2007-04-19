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

import os

import gtk

from configobj import ConfigObj

from kiwi.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView


class OpenWithItem(object):

    def __init__(self, section=None):
        if section is not None:
            self.name = section['name']
            self.command = section['command']
            self.glob = section['glob']
        else:
            self.name = 'unnamed'
            self.command = ''
            self.glob = '*'

    def as_dict(self):
        return dict(
            name=self.name,
            command=self.command,
            glob=self.glob,
        )

class OpenWithEditor(PidaGladeView):

    gladefile = 'openwith-editor'

    def create_ui(self):
        self.items_ol.set_columns([
            Column('name'),
            Column('command'),
            Column('glob'),
        ])
        self._current = None

    def prefill(self, config):
        for section in config:
            item = OpenWithItem(config[section])
            self.items_ol.append(item)

    def set_current(self, item):
        self._current = item
        self.name_entry.set_text(item.name)
        self.command_entry.set_text(item.command)
        self.glob_entry.set_text(item.glob)

    def on_new_button__clicked(self, button):
        new = OpenWithItem()
        self.items_ol.append(new, select=True)

    def on_save_button__clicked(self, button):
        self.svc.save([i for i in self.items_ol])

    def on_items_ol__selection_changed(self, ol, item):
        self.set_current(item)

    def on_name_entry__changed(self, entry):
        self._current.name = entry.get_text()
        self.items_ol.update(self._current)

    def on_command_entry__changed(self, entry):
        self._current.command = entry.get_text()
        self.items_ol.update(self._current)

    def on_glob_entry__changed(self, entry):
        self._current.glob = entry.get_text()
        self.items_ol.update(self._current)


class OpenWithActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_openwith',
            TYPE_TOGGLE,
            'Configure Open With',
            'Show the Open With Editor',
            'configuration',
            self.on_show_openwith,
            '<Shift><Control>['
        )

        self.create_action(
            'openwith-for-file',
            TYPE_NORMAL,
            'Open With',
            'Open a file with',
            gtk.STOCK_OPEN,
            self.on_openwith_for_file,
        )

    def on_show_openwith(self, action):
        if action.get_active():
            self.svc.show_editor()
        else:
            self.svc.hide_editor()

    def on_openwith_for_file(self, action):
        menuitem = action.get_proxies()[0]
        menuitem.remove_submenu()
        menu = gtk.Menu()
        menuitem.set_submenu(menu)
        for item in self.svc.get_items():
            act = gtk.Action(item.name, item.name, item.command, gtk.STOCK_EXECUTE)
            act.connect('activate', self.on_open_with, action.contexts_kw, item)
            mi = act.create_menu_item()
            menu.append(mi)
        menu.append(gtk.SeparatorMenuItem())
        act = self.svc.get_action('show_openwith')
        menu.append(act.create_menu_item())
        menu.show_all()

    def on_open_with(self, action, contexts_kw, item):
        filename = contexts_kw['file_name']
        command = item.command % filename
        self.svc.boss.cmd('commander', 'execute',
            commandargs=['bash', '-c', command])


class OpenWithFeatures(FeaturesConfig):

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'openwith-file-menu.xml'))

# Service class
class Openwith(Service):
    """Describe your Service Here""" 
    actions_config = OpenWithActions
    features_config = OpenWithFeatures

    def pre_start(self):
        self._filename = os.path.join(self.boss.get_pida_home(), 'openwith.ini')
        self._config = ConfigObj(self._filename)
        self._view = OpenWithEditor(self)
        self._view.prefill(self._config)

    def show_editor(self):
        self.boss.cmd('window', 'add_detached_view', paned='Plugin',
                      view=self._view)

    def hide_editor(self):
        self.boss.cmd('window', 'remove_view', view=self._view)
        
    def save(self, items):
        self._config.clear()
        for item in items:
            self._config[item.name] = item.as_dict()
            self._config.write()

    def get_items(self):
        for section in self._config:
            yield OpenWithItem(self._config[section])
        

# Required Service attribute for service loading
Service = Openwith



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
