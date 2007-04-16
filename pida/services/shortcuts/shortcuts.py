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
        self.doc = svc.__doc__
        self.stock_id = ''
        

class ShortcutsView(PidaView):

    def create_ui(self):
        self.shortcuts_list = ObjectTree(
            [
                Column('stock_id', use_stock=True),
                Column('label', sorted=True),
                Column('doc'),
                Column('value'),
            ]
        )
        self.shortcuts_list.set_headers_visible(False)
        self._current = None
        self.shortcuts_list.connect('selection-changed',
                                    self._on_selection_changed)
        self.shortcuts_list.connect('double-click',
                                    self._on_list_double_click)
        vbox = gtk.VBox(spacing=6)
        vbox.set_border_width(6)
        self.add_main_widget(vbox)
        for service in self.svc.boss.get_services():
            if len(service.get_keyboard_options()):
                sli = ServiceListItem(service)
                self.shortcuts_list.append(None, sli)
                for opt in service.get_keyboard_options().values():
                    self.shortcuts_list.append(sli, opt)
        self.shortcuts_list.show_all()
        hbox = gtk.HBox(spacing=6)
        l = gtk.Label('Capture Shortcut')
        hbox.pack_start(l, expand=False)
        self._capture_entry = gtk.Entry()
        hbox.pack_start(self._capture_entry)
        self._capture_entry.connect('key-press-event',
                                    self._on_capture_keypress)
        self._capture_entry.set_sensitive(False)
        vbox.pack_start(self.shortcuts_list)
        vbox.pack_start(hbox, expand=False)
        vbox.show_all()

    def decorate_service(self, service):
        return ServiceListItem(service)

    def _on_selection_changed(self, otree, item):
        if isinstance(item, ServiceListItem):
            self._current = None
            self._capture_entry.set_sensitive(False)
            self._capture_entry.set_text('')
        else:
            self._current = item
            self._capture_entry.set_sensitive(True)
            self._capture_entry.set_text(item.value)

    def _on_list_double_click(self, otree, item):
        self._capture_entry.grab_focus()
        self._capture_entry.select_region(0, -1)

    def _on_capture_keypress(self, entry, event):
        # svn.gnome.org/viewcvs/gazpacho/trunk/gazpacho/actioneditor.py
        # Tab must be handled as normal. Otherwise we can't move from
        # the entry.
        if event.keyval == gtk.keysyms.Tab:
            return False
        modifiers = event.get_state() & gtk.accelerator_get_default_mod_mask()
        modifiers = int(modifiers)
        # Check if we should clear the entry
        clear_keys = [gtk.keysyms.Delete,
                      gtk.keysyms.KP_Delete,
                      gtk.keysyms.BackSpace]
        if modifiers == 0:
            if event.keyval in clear_keys:
                entry.set_text('')
            return True
        # Check if the accelerator is valid and add it to the entry
        if gtk.accelerator_valid(event.keyval, modifiers):
            accelerator = gtk.accelerator_name(event.keyval, modifiers)
            entry.set_text(accelerator)
            self._current.value = accelerator
        return True

class ShortcutsActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_shortcuts',
            TYPE_TOGGLE,
            'Edit Shortcuts',
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
