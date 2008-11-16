# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import gtk

from kiwi.ui.objectlist import ObjectTree, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.actions import ActionsConfig, TYPE_TOGGLE
from pida.core.events import  EventsConfig

from pida.ui.views import PidaView

# locale
from pida.core.locale import Locale
locale = Locale('shortcuts')
_ = locale.gettext

class ServiceListItem(object):
    
    def __init__(self, svc):
        self._svc = svc
        self.label = self.no_mnemomic_label = svc.get_name().capitalize()
        self.doc = ''
        self.stock_id = ''
        

class ShortcutsView(PidaView):

    key = "shortcuts.view"

    icon_name = 'key_bindings'
    label_text = _('Shortcuts')

    def create_ui(self):
        self.shortcuts_list = ObjectTree(
            [
                Column('stock_id', use_stock=True),
                Column('no_mnemomic_label', sorted=True),
                Column('value'),
                Column('doc'),
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
        self.update()
        self.shortcuts_list.show_all()
        hbox = gtk.HBox(spacing=6)
        l = gtk.Label(_('Capture Shortcut'))
        hbox.pack_start(l, expand=False)
        self._capture_entry = gtk.Entry()
        hbox.pack_start(self._capture_entry)
        self._capture_entry.connect('key-press-event',
                                    self._on_capture_keypress)
        self._capture_entry.set_sensitive(False)
        self._full_button = gtk.ToggleButton('Full')
        hbox.pack_start(self._full_button)
        vbox.pack_start(self.shortcuts_list)
        vbox.pack_start(hbox, expand=False)
        vbox.show_all()
        self.get_toplevel().set_size_request(350, 0)

    def update(self):
        self.shortcuts_list.clear()
        for service in self.svc.boss.get_services() + [
                                self.svc.boss.editor]:
            if len(service.get_keyboard_options()):
                sli = ServiceListItem(service)
                self.shortcuts_list.append(None, sli)
                for opt in service.get_keyboard_options().values():
                    self.shortcuts_list.append(sli, opt)

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
            self._capture_entry.set_text(item and item.value or "")

    def _on_list_double_click(self, otree, item):
        self._capture_entry.grab_focus()
        self._capture_entry.select_region(0, -1)

    def _on_capture_keypress(self, entry, event):
        # svn.gnome.org/viewcvs/gazpacho/trunk/gazpacho/actioneditor.py
        # Tab must be handled as normal. Otherwise we can't move from
        # the entry.
        if event.keyval == gtk.keysyms.Tab and not self._full_button.get_active():
            return False
        modifiers = event.get_state() & gtk.accelerator_get_default_mod_mask()
        modifiers = int(modifiers)
        # Check if we should clear the entry
        clear_keys = [gtk.keysyms.Delete,
                      gtk.keysyms.KP_Delete,
                      gtk.keysyms.BackSpace]
        if modifiers == 0 and not self._full_button.get_active():
            if event.keyval in clear_keys:
                entry.set_text('')
            return True
        # Check if the accelerator is valid and add it to the entry
        if gtk.accelerator_valid(event.keyval, modifiers) or self._full_button.get_active():
            accelerator = gtk.accelerator_name(event.keyval, modifiers)
            entry.set_text(accelerator)
            self._current.set_value(accelerator)
        return True

    def can_be_closed(self):
        self.svc.get_action('show_shortcuts').set_active(False)


class ShortcutsEventConfig(EventsConfig):
    
    def subscribe_all_foreign(self):
        self.subscribe_foreign('plugins', 'plugin_stopped', 
                               self.on_plugin_changed)
        self.subscribe_foreign('plugins', 'plugin_started', 
                               self.on_plugin_changed)

    def on_plugin_changed(self, *args, **kwargs):
        if self.svc.started:
            self.svc._view.update()

class ShortcutsActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_shortcuts',
            TYPE_TOGGLE,
            _('Edit Shortcuts'),
            _('Show the PIDA keyboard shortcut editor'),
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
    events_config = ShortcutsEventConfig

    def pre_start(self):
        self._view = None

    def start(self):
        self._view = ShortcutsView(self)

        acts = self.boss.get_service('window').actions

        acts.register_window(self._view.key,
                             self._view.label_text)


    def show_shortcuts(self):
        self.boss.cmd('window', 'add_view',
            paned='Plugin', view=self._view)

    def hide_shortcuts(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def update(self):
        if self._view:
            self._view.update()

# Required Service attribute for service loading
Service = Shortcuts



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
