# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import gtk

from pygtkhelpers.ui.objectlist import ObjectTree, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE
from pida.core.events import  EventsConfig

from pida.ui.views import PidaView, WindowConfig

# locale
from pida.core.locale import Locale
locale = Locale('shortcuts')
_ = locale.gettext

class ServiceListItem(object):

    def __init__(self, svc):
        self.svc = svc
        self.label = self.no_mnemomic_label = svc.get_name().capitalize()
        self.doc = ''
        self.value = ''
        self.stock_id = ''

    def __repr__(self):
        return '<SLI %s>' % self.label.lower()

class ShortcutsView(PidaView):

    key = "shortcuts.view"

    icon_name = 'key_bindings'
    label_text = _('Shortcuts')

    def create_ui(self):
        self.shortcuts_list = ObjectTree([
            Column('stock_id', use_stock=True),
            Column('no_mnemomic_label', sorted=True, searchable=True),
            Column('value', searchable=True),
            Column('doc', searchable=True),
        ])
        self.shortcuts_list.set_headers_visible(False)
        self._current = None
        self.shortcuts_list.connect('selection-changed',
                                    self._on_selection_changed)
        self.shortcuts_list.connect('item-activated',
                                    self._on_list_double_click)
        vbox = gtk.VBox(spacing=6)
        vbox.set_border_width(6)
        self.add_main_widget(vbox)
        self.update()
        self.shortcuts_list.show_all()
        hbox = gtk.VBox(spacing=6)
        bbox = gtk.HBox(spacing=6)
        l = gtk.Label(_('Capture Shortcut'))
        hbox.pack_start(l, expand=False)
        self._capture_entry = gtk.Entry()
        hbox.pack_start(self._capture_entry)
        self._capture_entry.connect('key-press-event',
                                    self._on_capture_keypress)
        self._capture_entry.connect('focus-in-event',
                                    self._on_focus_in)
        self._capture_entry.connect('focus-out-event',
                                    self._on_focus_out)
        self._capture_entry.set_sensitive(False)
        self._default_button = gtk.Button(_('Default'))
        self._default_button.connect('clicked',
                                    self._on_default_clicked)

        self._clear_button = gtk.Button(_('Clear'))
        self._clear_button.connect('clicked',
                                    self._on_clear_clicked)

        self._full_button = gtk.ToggleButton(_('Allow All'))
        self._full_button.set_tooltip_markup(
            _("This allows you to bind all/confusing keys to a shortcut (be warned :-))"))
        hbox.pack_start(bbox)
        bbox.pack_start(self._default_button)
        bbox.pack_start(self._clear_button)
        bbox.pack_start(self._full_button)
        vbox.pack_start(self.shortcuts_list)
        vbox.pack_start(hbox, expand=False)
        vbox.show_all()
        self.get_toplevel().set_size_request(350, 0)

    def update(self):
        self.shortcuts_list.clear()
        for service in self.svc.boss.get_services():
            opts = service.get_keyboard_options().values()
            if opts:
                sli = ServiceListItem(service)
                self.shortcuts_list.append(sli)
                for opt in opts:
                    self.shortcuts_list.append(opt, parent=sli)

    def _on_selection_changed(self, otree):
        item = otree.selected_item
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

    def _on_clear_clicked(self, event):
        self._capture_entry.set_text('')
        self._current.set_value('')

    def _on_default_clicked(self, event):
        self._capture_entry.set_text(self._current.default)
        self._current.set_value(self._current.default)

    def _on_focus_in(self, dummy1, dummy2):
        for service in self.svc.boss.get_services() + [
                                self.svc.boss.editor]:
            service.get_action_group().set_sensitive(False)

    def _on_focus_out(self, dummy1, dummy2):
        for service in self.svc.boss.get_services() + [
                                self.svc.boss.editor]:
            service.get_action_group().set_sensitive(True)

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
                self._current.set_value('')
            return True
        # Check if the accelerator is valid and add it to the entry
        if gtk.accelerator_valid(event.keyval, modifiers) or \
           self._full_button.get_active():
            accelerator = gtk.accelerator_name(event.keyval, modifiers)
            if self.free_accelerator(accelerator, self._current):
                entry.set_text(accelerator)
                self._current.set_value(accelerator)
            # deactive the dangerouse button again :-)
            self._full_button.set_active(False)
        return True

    def free_accelerator(self, accelerator, setfor):
        """
        Test if a accelerator is free and if not ask the user if it should
        be freed
        
        @return True if accelerator is free
        """
        for service in self.svc.boss.get_services() + [
                                self.svc.boss.editor]:
            if len(service.get_keyboard_options()):
                for opt in service.get_keyboard_options().values():
                    if opt.value == accelerator and opt != setfor:
                        if self.svc.yesno_dlg(
                            _("Shortcut is already in use by: %s/%s\n"
                              "Should it be cleared ?" 
                                %(service.get_label(),
                                  opt.no_mnemomic_label))):
                            opt.set_value('')
                        else:
                            return False
        return True

    def can_be_closed(self):
        self.svc.get_action('show_shortcuts').set_active(False)


class ShortcutsEventConfig(EventsConfig):

    def create(self):
        self.publish('shortcut_changed')
        self.subscribe('shortcut_changed', self.on_shortcut_changed)

    def subscribe_all_foreign(self):
        self.subscribe_foreign('plugins', 'plugin_stopped', 
                               self.on_plugin_changed)
        self.subscribe_foreign('plugins', 'plugin_started', 
                               self.on_plugin_changed)

    def on_plugin_changed(self, *args, **kwargs):
        if self.svc.started:
            self.svc._view.update()

    def on_shortcut_changed(self):
        try:
            if self.svc._view.toplevel.window.is_visible():
                self.svc._view.shortcuts_list.refresh()
        except AttributeError, e:
            # window may not exist or was not realized yet
            pass

class ShortcutsActionsConfig(ActionsConfig):

    def create_actions(self):
        WindowConfig.action = self.create_action(
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

class ShortcutsWindowConfig(WindowConfig):
    key = ShortcutsView.key
    label_text = ShortcutsView.label_text

class ShortcutsFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            ShortcutsWindowConfig)

# Service class
class Shortcuts(Service):
    """Describe your Service Here""" 
    
    actions_config = ShortcutsActionsConfig
    events_config = ShortcutsEventConfig
    features_config = ShortcutsFeaturesConfig

    def pre_start(self):
        self._view = None

    def start(self):
        self._view = ShortcutsView(self)

    def show_shortcuts(self):
        self.boss.cmd('window', 'add_view',
            paned='Plugin', view=self._view)

    def hide_shortcuts(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def update(self):
        if not self.started:
            return
        if self._view:
            self._view.update()

# Required Service attribute for service loading
Service = Shortcuts



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
