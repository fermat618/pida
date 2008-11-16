# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.options import OptionsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

# locale
from pida.core.locale import Locale
locale = Locale('appcontroller')
_ = locale.gettext

class AppcontrollerConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
            'open_workspace_manager',
            _('Always show workspace manager'),
            bool,
            True,
            _('Always open the workspace manager when no workspace name is given'),
        )

class AppcontrollerActions(ActionsConfig):

    dbus_no_activate = ('quit_pida',)

    def create_actions(self):
        self.create_action(
            'quit_pida',
            TYPE_NORMAL,
            _('Quit PIDA'),
            _('Exit the application'),
            gtk.STOCK_QUIT,
            self.on_quit_pida,
            '<Control><Alt>q'
        )

    def on_quit_pida(self, action):
        self.svc.boss.stop()
        

# Service class
class Appcontroller(Service):
    """Describe your Service Here""" 

    actions_config = AppcontrollerActions
    options_config = AppcontrollerConfig

# Required Service attribute for service loading
Service = Appcontroller



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
