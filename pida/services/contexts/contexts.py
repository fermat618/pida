# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import pkgutil
import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig


CONTEXT_TYPES = [
    'file-menu',
    'dir-menu',
    'url-menu',
]

class ContextFeaturesConfig(FeaturesConfig):

    def create(self):
        for context in CONTEXT_TYPES:
            self.publish(context)

class ContextCommandsConfig(CommandsConfig):

    def get_menu(self, context, **kw):
        return self.svc.get_menu(context, **kw)

    def popup_menu(self, context, event=None, **kw):
        handler_id = 0
        menu = self.get_menu(context, **kw)
        menu.show_all()
        if event is None:
            button = 3
            time = gtk.get_current_event_time()
        else:
            button = event.button
            time = event.time

            def on_menu_deactivated(menu):
                menu.handler_disconnect(handler_id)
                self.svc.emit('menu-deactivated', menu=menu, context=context, **kw)

        handler_id = menu.connect('deactivate', on_menu_deactivated)
        self.svc.emit('show-menu', menu=menu, context=context, **kw)
        menu.popup(None, None, None, button, time)

class ContextEventsConfig(EventsConfig):

    def create(self):
        self.publish('show-menu')
        self.publish('menu-deactivated')
    
    def subscribe_all_foreign(self):
        self.subscribe_foreign('plugins', 'plugin_started',
            self.plugins_changed)
        self.subscribe_foreign('plugins', 'plugin_stopped',
            self.plugins_changed)

    def plugins_changed(self, plugin):
        self.svc.create_uims()


# Service class
class Contexts(Service):
    """Describe your Service Here""" 

    features_config = ContextFeaturesConfig
    commands_config = ContextCommandsConfig
    events_config = ContextEventsConfig

    def start(self) :
        self.create_uims()

    def create_uims(self):
        self._uims = {}
        for context in CONTEXT_TYPES:
            uim = self._uims[context] = gtk.UIManager()
            uim.add_ui_from_string(self.get_base_ui_definition(context))
            for service, uidef in self.features[context]:
                ag = service.get_action_group()
                uim.insert_action_group(ag, 0)
                if not uidef.startswith('uidef'):
                    uidef = 'uidef/'+uidef
                uidef_data = pkgutil.get_data(service.__module__, uidef)
                uim.add_ui_from_string(uidef_data)

    def get_base_ui_definition(self, context):
        file_name = 'uidef/%s.xml' % context
        return pkgutil.get_data(__name__, file_name)

    def get_menu(self, context, **kw):
        for group in self._uims[context].get_action_groups():
            for action in group.list_actions():
                action.contexts_kw = kw
        menu = self._uims[context].get_toplevels('popup')[0]
        return menu



# Required Service attribute for service loading
Service = Contexts



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
