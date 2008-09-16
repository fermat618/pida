# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005-2006 The PIDA Project

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


''' A library to embed vim in a gtk socket '''


import gtk
import os, uuid


import subprocess

class VimEmbedWidget(gtk.EventBox):

    def __init__(self, command, script_path, uid, args=[]):
        gtk.EventBox.__init__(self)
        self.server_name = uid
        self._command = command
        self._init_script = script_path
        self.pid = None
        self.args = args
        self.r_cb_plugged = None
        self.r_cb_unplugged = None
        self.__eb = None

    def _create_ui(self):
        socket = gtk.Socket()
        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.add(socket)
        self.show_all()
        return socket.get_id()

    def should_remove(self):
        self.service.remove_attempt()
        return False

    def run(self):
        print 'running'

        xid = self._create_ui()

        print 'xid', xid
        if not xid:
            return
        print 'xid', self.pid
        if not self.pid:
            print 'runn'
            try:
                env = os.environ.copy()
                env['PIDA_DBUS_UID'] = self.server_name
                popen = subprocess.Popen(
                    [self._command,
                    '--servername', self.server_name,
                    '--cmd', 'let PIDA_EMBEDDED=1',
                    '--cmd', 'so %s' % self._init_script,
                    '--socketid', str(xid),
                    ] + self.args,
                    close_fds=True,
                    env=env
                )
                self.pid = popen.pid
                print popen
            except OSError:
                raise
                return False
        self.show_all()
        return True

    def grab_input_focus(self):
        self.child_focus(gtk.DIR_TAB_FORWARD)

