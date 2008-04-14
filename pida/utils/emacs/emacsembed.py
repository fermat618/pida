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

"""This module provides the widget which is responsible to embed Emacs for Pida.

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
        """Start the Emacs process."""
        if not self._pid:
            xid = self._create_ui()
            if xid:
                args = ['--parent-id', '%s' % xid,
                        '-l', '%s' % self._init_script]
                                 
                args.extend(self._args)
                # -f server-start has to be the last argument!
                args.extend(['-f', 'server-start'])
                popen = subprocess.Popen([self._command] + args, 
                                         close_fds=True)
                self._pid = popen.pid
        self.show_all()

    def grab_input_focus(self):
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
