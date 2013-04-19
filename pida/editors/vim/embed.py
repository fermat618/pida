# -*- coding: utf-8 -*-

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    A library to embed vim in a gtk socket

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import os


import subprocess

#XXX: the problem may not be here.
os.environ['PIDA_BASE'] = os.path.dirname(
                          os.path.dirname(
                          os.path.dirname(
                          os.path.dirname(__file__))))


class VimStarter(gtk.EventBox):

    def __init__(self, command, script_path, args=None):
        gtk.EventBox.__init__(self)
        self.command = command
        self.init_script = script_path
        self.pid = None
        self.args = args or []

    def run(self):
        if not self.pid:
            try:
                popen = subprocess.Popen(
                    [self.command,
                    # XXX: leftover from vim com
                    #'--servername', self.server_name,
                    '--cmd', 'let PIDA_EMBEDDED=1',
                    '-S', '%s' % self.init_script,
                    ] + self.args,
                    close_fds=True,
                )
                self.pid = popen.pid
            except OSError:
                raise
                return False
        self.show_all()
        return True


class VimEmbedWidget(gtk.EventBox):

    def __init__(self, command, script_path, args=None):
        gtk.EventBox.__init__(self)
        self._command = command
        self._init_script = script_path
        self.pid = None
        self.args = args or []
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

        xid = self._create_ui()

        if not xid:
            return
        if not self.pid:
            try:
                popen = subprocess.Popen(
                    [self._command,
                    # XXX: leftover from vim com
                    #'--servername', self.server_name,
                    '--cmd', 'let PIDA_EMBEDDED=1',
                    '-S', '%s' % self._init_script,
                    '--socketid', str(xid),
                    ] + self.args,
                    close_fds=True,
                )
                self.pid = popen.pid
            except OSError:
                raise
                return False
        self.show_all()
        return True

    def grab_input_focus(self):
        self.child_focus(gtk.DIR_TAB_FORWARD)
