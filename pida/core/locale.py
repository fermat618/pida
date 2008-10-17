# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import gettext
import os
import gtk.glade

class Locale(object):

    def __init__(self, modulename):
        self.modulename = modulename
        self.localepath = self.get_base_locale_directory()
        gettext.bindtextdomain(self.modulename, self.localepath)
        gettext.textdomain(self.modulename)

    def get_base_locale_directory(self):
        # except for main pida
        if self.modulename == 'pida':
            return os.path.join(os.path.dirname(
                    os.path.dirname(__file__)), 'resources', 'locale')
        # for service/plugin
        return os.path.join(os.path.dirname(
                os.path.dirname(__file__)), 'services', self.modulename, 'locale')

    def gettext(self, message):
        return gettext.dgettext(self.modulename, message)

    def bindglade(self):
        gtk.glade.bindtextdomain(self.modulename, self.localepath)
        gtk.glade.textdomain(self.modulename)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
