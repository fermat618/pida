# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
from gtk import gdk

# PIDA Imports
import pida
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.core.environment import get_pixmap_path


# locale
from pida.core.locale import Locale
locale = Locale('help')
_ = locale.gettext

class PidaAboutDialog(gtk.AboutDialog):

    def __init__(self, boss):
        gtk.AboutDialog.__init__(self)
        self.set_transient_for(boss.window)
        self.set_name('pida')
        self.set_version(pida.version)
        self.set_logo(self._create_logo())
        self.set_copyright(pida.copyright)
        self.set_license(
            'GNU GPL Version 2 (or at your choice any later) '
             'as published by the FSF'
        )
        self.set_wrap_license(True)
        self.set_authors(pida.authors)
        self.set_website(pida.website)
        self.set_comments(pida.short_description)

    def _create_logo(self):
        pb = gdk.pixbuf_new_from_file_at_size(
            get_pixmap_path('pida-icon.svg'), 128, 128)
        return pb

class HelpActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'help_about',
            TYPE_NORMAL,
            _('About'),
            _('About PIDA'),
            gtk.STOCK_HELP,
            self.show_about_dialog
        )

    def show_about_dialog(self, action):
        dialog = PidaAboutDialog(self.svc.boss)
        resp = dialog.run()
        dialog.destroy()

# Service class
class Help(Service):
    """Describe your Service Here""" 

    actions_config = HelpActionsConfig

# Required Service attribute for service loading
Service = Help



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
