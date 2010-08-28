# -*- coding: utf-8 -*-
"""
    This module provides the widget 
    which is responsible to embed Emacs for Pida.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)


This work was made possible thanks to the Emacs patches written by Timo Savola
for his own embedding of Emacs with his Encode project
(http://encode.sourceforge.net/).
"""

import subprocess
import gtk

class EmacsEmbedWidget(gtk.EventBox):
    """A widget embedding Emacs.
    
    The EmacsEmbedWidget makes use of a GTK socket to embed an Emacs frame inside
    a GTK application. The widget is also a GTK Event Box, so key events are
    available.
    """

    def __init__(self, command, script_path, args=[]):
        """Constructor."""
        gtk.EventBox.__init__(self)
        self._command = command
        self._init_script = script_path
        self._pid = None
        self._args = args

    def run(self):
        """Start the editor using Popen"""
        if not self._pid:
            xid = self._create_ui()
            if xid:
                args = ['--parent-id', '%s' % xid,
                        '-l', '%s' % self._init_script]
                args.extend(self._args)
                popen = subprocess.Popen([self._command] + args, 
                                         close_fds=True)
                self._pid = popen.pid
        self.show_all()

    def grab_input_focus(self):
        """Give focus to editor"""
        self.child_focus(gtk.DIR_TAB_FORWARD)

    def _create_ui(self):
        """Instantiate the GTK socket.

        Called by the run method before the widget is realized.
        """
        socket = gtk.Socket()
        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.add(socket)
        self.show_all()
        return socket.get_id()
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
