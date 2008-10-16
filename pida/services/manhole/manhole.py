# -*- coding: utf-8 -*-
"""
    The debug python shell

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.ui.views import PidaView

from pida.utils.pyconsole import Console

# locale
from pida.core.locale import Locale
locale = Locale('manhole')
_ = locale.gettext

class ManholeActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_manhole',
            TYPE_TOGGLE,
            _('PIDA Internal Shell'),
            _('Open the PIDA Internal Shell'),
            'face-monkey',
            self.on_show_manhole,
            '<Shift><Control>M',
        )

    def on_show_manhole(self, action):
        if action.get_active():
            self.svc.show_manhole()
        else:
            self.svc.hide_manhole()

class ManholeView(PidaView):

    key = 'manhole.shell'
    icon_name = 'face-monkey'

    label_text = _('Debug PIDA')

    def create_ui(self):
        console = Console(locals=self.svc.get_local_dict(),
                          banner=_("PIDA Shell. Keep breathing."),
                          use_rlcompleter=False)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(console)
        sw.show_all()
        self.add_main_widget(sw)

    def can_be_closed(self):
        self.svc.get_action('show_manhole').set_active(False)

# Service class
class Manhole(Service):
    """Describe your Service Here""" 

    actions_config = ManholeActionsConfig
    
    def start(self):
        self._view = ManholeView(self)

    def show_manhole(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)

    def hide_manhole(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def get_local_dict(self):
        return dict(boss=self.boss)

# Required Service attribute for service loading
Service = Manhole



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
