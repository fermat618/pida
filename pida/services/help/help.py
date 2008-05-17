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
from gtk import gdk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.core.environment import get_pixmap_path

from pida import PIDA_NAME, PIDA_VERSION, PIDA_AUTHORS, PIDA_COPYRIGHT, \
                 PIDA_LICENSE, PIDA_WEBSITE, PIDA_SHORT_DESCRIPTION


# locale
from pida.core.locale import Locale
locale = Locale('help')
_ = locale.gettext

class PidaAboutDialog(gtk.AboutDialog):

    def __init__(self, boss):
        gtk.AboutDialog.__init__(self)
        self.set_transient_for(boss.window)
        self.set_name(PIDA_NAME)
        self.set_version(PIDA_VERSION)
        self.set_logo(self._create_logo())
        self.set_copyright(PIDA_COPYRIGHT)
        self.set_license(PIDA_LICENSE)
        self.set_wrap_license(True)
        self.set_authors(PIDA_AUTHORS)
        self.set_website(PIDA_WEBSITE)
        self.set_comments(PIDA_SHORT_DESCRIPTION)

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
