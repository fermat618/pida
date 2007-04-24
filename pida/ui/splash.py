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

from pida.utils.testing import refresh_gui

class SplashScreen(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_decorated(False)
        vb = gtk.VBox()
        self.add(vb)
        l = gtk.Label('PIDA is starting...')
        l.set_alignment(0.5, 1)
        l.show()
        vb.pack_start(l)
        l = gtk.Label()
        l.set_markup('and it <b>loves</b> you!')
        l.set_alignment(0.5, 0)
        l.show()
        vb.pack_start(l)
        vb.show()
        self.resize(200, 75)

    def show_splash(self):
        refresh_gui()
        refresh_gui()
        self.show()
        refresh_gui()
        refresh_gui()

    def hide_splash(self):
        self.hide_all()
        self.destroy()






# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
