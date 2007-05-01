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

import os, glob

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

    def match(self, file_name):
        return glob.fnmatch.fnmatch(file_name, self.glob)

class OpenWithEditor(PidaGladeView):

    gladefile = 'openwith-editor'
    icon_name = gtk.STOCK_OPEN
    label_text = 'Open With'

    def create_ui(self):
        self.items_ol.set_columns([
            Column('name'),
            Column('command'),
            Column('glob'),
        ])
        self._current = None
        self._block_changed = False

    def prefill(self, config):
        for section in config:
            item = OpenWithItem(config[section])
            self.items_ol.append(item)

    def set_current(self, item):
        self._current = item
        self._block_changed = True
        if item is None:
            self.name_entry.set_text('')
            self.command_entry.set_text('')
            self.glob_entry.set_text('')
            self.attrs_table.set_sensitive(False)
            self.delete_button.set_sensitive(False)
        else:
            self.name_entry.set_text(item.name)
            self.command_entry.set_text(item.command)
            self.glob_entry.set_text(item.glob)
            self.attrs_table.set_sensitive(True)
            self.delete_button.set_sensitive(True)
        self._block_changed = False

    def on_new_button__clicked(self, button):
        new = OpenWithItem()
        self.items_ol.append(new, select=True)
        self.save_button.set_sensitive(True)

    def on_save_button__clicked(self, button):
        self.svc.save([i for i in self.items_ol])
        self.save_button.set_sensitive(False)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_openwith').set_active(False)

    def on_delete_button__clicked(self, button):
        if self.svc.boss.get_window().yesno_dlg(
                'Are you sure you want to delete %s' % self._current.name):
            self.items_ol.remove(self._current, select=True)
            self.save_button.set_sensitive(True)

    def on_items_ol__selection_changed(self, ol, item):
        self.set_current(item)

    def on_name_entry__changed(self, entry):
        if not self._block_changed:
            self._current.name = entry.get_text()
            self.item_changed()

    def on_command_entry__changed(self, entry):
        if not self._block_changed:
            self._current.command = entry.get_text()
            self.item_changed()

    def on_glob_entry__changed(self, entry):
        if not self._block_changed:
            self._current.glob = entry.get_text()
            self.item_changed()

    def item_changed(self):
        self.save_button.set_sensitive(True)
        self.items_ol.update(self._current)


class OpenWithActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_openwith',
            TYPE_TOGGLE,
            'Configure Open With',
            'Show the Open With Editor',
            'gnome-settings',
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
            'NOACCEL',
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
        file_name = action.contexts_kw['file_name']
        for item in self.svc.get_items_for_file(file_name):
            act = gtk.Action(item.name, item.name, item.command, gtk.STOCK_EXECUTE)
            act.connect('activate', self.on_open_with, file_name, item)
            mi = act.create_menu_item()
            menu.append(mi)
        menu.append(gtk.SeparatorMenuItem())
        act = self.svc.get_action('show_openwith')
        menu.append(act.create_menu_item())
        menu.show_all()

    def on_open_with(self, action, file_name, item):
        command = item.command % file_name
        self.svc.boss.cmd('commander', 'execute',
            commandargs=['bash', '-c', command], title=item.name,
            icon=gtk.STOCK_OPEN)


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
        self.boss.cmd('window', 'add_view', paned='Plugin',
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

    def get_items_for_file(self, file_name):
        for item in self.get_items():
            if item.match(file_name):
                yield item
        

# Required Service attribute for service loading
Service = Openwith



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
