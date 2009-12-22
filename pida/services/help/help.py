# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import os
from gtk import gdk

# PIDA Imports
import pida
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL


# locale
from pida.core.locale import Locale
locale = Locale('help')
_ = locale.gettext

#FIXME: this seems so wrong, but how to detect the docs directory correctly
prefix_lst = []

def build_path(prefix):
    return os.path.abspath(os.path.join(prefix, "share", "doc", "pida", "html"))

if __file__.find('site-packages') != -1:
    prefix_lst.append(build_path(
                      os.path.join(__file__[:__file__.find('site-packages')], 
                      os.pardir, os.pardir)))
if __file__.find('dist-packages') != -1:
    prefix_lst.append(build_path(
                      os.path.join(__file__[:__file__.find('dist-packages')], 
                      os.pardir, os.pardir)))


prefix_lst += [os.path.abspath(os.path.join(os.path.dirname(__file__), 
                               os.pardir, os.pardir, os.pardir, 
                               'docs', '_build', 'html')),
              build_path("/usr/local"),
              build_path("/usr"),
              build_path(os.path.expanduser("~")),
              ]

class PidaAboutDialog(gtk.AboutDialog):
    """About dialog"""
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
        self.set_authors([_("Core Developers:")] + pida.dev_core + \
                         ["", _("Contributors:")] + pida.dev_contrib)
        self.set_website(pida.website)
        self.set_comments(pida.short_description)

    def _create_logo(self):
        pb = gdk.pixbuf_new_from_file_at_size(
            os.path.join(
                pida.__path__[0], 
                'resources/pixmaps/pida-icon.svg'),
            128, 128)
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
        self.create_action(
            'help_doc',
            TYPE_NORMAL,
            _('Documentation'),
            _('Show Documentation'),
            gtk.STOCK_ABOUT,
            self.show_docs
        )

    def show_about_dialog(self, action):
        dialog = PidaAboutDialog(self.svc.boss)
        resp = dialog.run()
        dialog.destroy()

    def show_docs(self, action):
        for path in prefix_lst:
            if os.path.exists(path):
                self.svc.boss.cmd("browseweb", "browse", 
                                  url="file://%s/index.html" %path)
                return
        self.svc.boss.cmd("browseweb", "browse", 
                          url="http://docs.pida.co.uk/%s/" %pida.version)


# Service class
class Help(Service):
    """Help Service""" 

    actions_config = HelpActionsConfig

# Required Service attribute for service loading
Service = Help



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
