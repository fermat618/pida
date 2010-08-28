# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk, gobject

from pida.utils.testing import refresh_gui
from pida.core.environment import get_pixmap_path

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

class SplashScreen(gtk.Window): 

    def __init__(self): 
        gtk.Window.__init__(self)
        self.set_decorated(False)
        vb = gtk.VBox()
        self.add(vb)
#         l = gtk.Label(_('PIDA is starting...'))
#         l.set_alignment(0.5, 1)
#         l.show()
#         vb.pack_start(l)
#         l = gtk.Label()
#         l.set_markup(_('and it <b>loves</b> you!'))
#         l.set_alignment(0.5, 0)
#         l.show()
        self.img = gtk.Image()
        self.img.set_from_file(get_pixmap_path('pida-splash.png'))
        vb.pack_start(self.img)
        self.img.show()
        self.p = gtk.ProgressBar()
        vb.pack_start(self.p)
        self.p.show()
        vb.show()
        self.resize(250, 270)
        self.p.set_text(_("Initialize"))
        self.p.set_fraction(0.05)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

    def show_splash(self):
        self.show()
        refresh_gui()

    def update_progress(self, percent, what):
        self.p.set_text(what)
        if percent:
            self.p.set_fraction(percent/100.0)
        else:
            self.p.set_fraction(0)
        while gtk.events_pending():
            gtk.main_iteration_do(block=False)

    def hide_splash(self):
        self.hide_all()
        self.destroy()






# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
