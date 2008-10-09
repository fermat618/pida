# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os, glob
from subprocess import Popen

import gtk

from pida.utils.configobj import ConfigObj

from kiwi.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.core.environment import pida_home

from pida.ui.views import PidaGladeView

# locale
from pida.core.locale import Locale
locale = Locale('openwith')
_ = locale.gettext

class OpenWithItem(object):

    def __init__(self, section=None):
        if section is not None:
            self.name = section['name']
            self.command = section['command']
            self.glob = section['glob']
            if section.has_key('terminal'):
                # the bad guy saves a boolean as text in openwith.ini but 
                # cannot restore it as a boolean later
                if (isinstance(section['terminal'], str)):
                    self.terminal = section['terminal'] == 'True'
                else:
                    self.terminal = section['terminal']
            else:
                # if ini is from an older version without terminal property
                self.terminal = True
        else:
            self.name = _('unnamed')
            self.command = ''
            self.glob = '*'
            self.terminal = True

    def as_dict(self):
        return dict(
            name=self.name,
            command=self.command,
            glob=self.glob,
            terminal=self.terminal,
        )

    def match(self, file_name):
        if file_name is None:
            return False
        return glob.fnmatch.fnmatch(file_name, self.glob)

class OpenWithEditor(PidaGladeView):

    key = 'openwith.editor'

    gladefile = 'openwith-editor'
    locale = locale
    icon_name = gtk.STOCK_OPEN
    label_text = _('Open With')

    def create_ui(self):
        self.items_ol.set_columns([
            Column('name', title=_('Name')),
            Column('command', title=_('Command')),
            Column('glob', title=_('Glob')),
            Column('terminal', title=_('Terminal'), radio=True, data_type=bool),
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
            self.terminal_checkbutton.set_active(True)
            self.attrs_table.set_sensitive(False)
            self.delete_button.set_sensitive(False)
        else:
            self.name_entry.set_text(item.name)
            self.command_entry.set_text(item.command)
            self.glob_entry.set_text(item.glob)
            self.terminal_checkbutton.set_active(item.terminal)
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
        if self.svc.yesno_dlg(
                _('Are you sure you want to delete %s') % self._current.name):
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

    def on_terminal_checkbutton__toggled(self, checkbutton):
        if not self._block_changed:
            self._current.terminal = checkbutton.get_active()
            self.item_changed()

    def item_changed(self):
        self.save_button.set_sensitive(True)
        self.items_ol.update(self._current)

    def can_be_closed(self):
        self.svc.get_action('show_openwith').set_active(False)

class OpenWithActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_openwith',
            TYPE_TOGGLE,
            _('Configure Open With'),
            _('Show the Open With Editor'),
            'gnome-settings',
            self.on_show_openwith,
            '<Shift><Control>['
        )

        self.create_action(
            'openwith-for-file',
            TYPE_NORMAL,
            _('Open With'),
            _('Open a file with'),
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
        if (item.terminal):
            self.svc.boss.cmd('commander', 'execute',
                commandargs=['bash', '-c', command], title=item.name,
                icon=gtk.STOCK_OPEN)
        else:
            Popen(command, shell=True)


class OpenWithFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc.get_action_group(), 'openwith-file-menu.xml'))

# Service class
class Openwith(Service):
    """Describe your Service Here""" 
    actions_config = OpenWithActions
    features_config = OpenWithFeatures

    def pre_start(self):
        self._filename = os.path.join(pida_home, 'openwith.ini')
        self._config = ConfigObj(self._filename)
        if not os.path.exists(self._filename):
            default = self.create_default_item()
            self._config[default.name] = default.as_dict()
            self._config.write()
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

    def create_default_item(self):
        print "create_default_item"
        return OpenWithItem(dict(name="See", glob="*", command="see %s",
            terminal=True))
        

# Required Service attribute for service loading
Service = Openwith



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
