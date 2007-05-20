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

"""Classes for both way communication wih Emacs.

Communication with Emacs process is handled by EmacsClient in the pIDA->Emacs
way, and EmacsServer the other way. On occurence of a message, EmacsServer
extracts a request name and arguments, and then tries to invoke the matching
method on a EmacsCallback object (see editor/emacs/emacs.py).
"""

import logging
import socket
import subprocess

import gobject

from pida.core.log import build_logger


class EmacsClient(object):
    """Tool for sending orders to emacs.

    EmacsClient class relies on the emacsclient binary.
    Note that this utility works with a server started from inside a running
    emacs instance. We assume for now that the emacs instance running in pida
    is the only one having a running server.
    """
    
    def __init__(self):
        """Constructor."""
        #TODO: I would like to use something like  here,
        #      but then the log will be printed three times.
        self._log = logging.getLogger('emacs')
        self._active = True

    def activate(self):
        """Allow communication.

        An EmacsClient object is activated by default.
        """
        self._active = True

    def inactivate(self):
        """Prevents sending any message to Emacs.

        This can be useful if Pida knows emacs has quit for example.
        """
        self._active = False

    def set_directory(self, path):
        self._send('(cd "%s")' % path)

    def open_file(self, filename):
        self._send('(find-file "%s")' % filename)

    def change_buffer(self, filename):
        self._send('(switch-to-buffer (get-file-buffer "%s"))' % filename)
        
    def save_buffer(self):
        self._send('(save-buffer)')

    def save_buffer_as(self, filename):
        self._send('(write-file "%s"))' % filename)

    def close_buffer(self, buffer):
        self._send('(kill-buffer (get-file-buffer "%s"))' % buffer)

    def cut(self):
        self._send('(kill-region (region-beginning) (region-end))')

    def copy(self):
        self._send('(kill-ring-save (region-beginning) (region-end))')

    def paste(self):
        self._send('(yank)')

    def goto_line(self, line):
        self._send('(goto-line %s)' % line)

    def revert_buffer(self):
        self._send('(revert-buffer)')

    def undo(self):
        self._send('(undo-only)')

    def redo(self):
        # Well... I'm still a bit disturbed with the undo / redo of Emacs
        self._send('(undo)')

    def quit(self):
        self._send('(kill-emacs)')

    def _send(self, command):
        """Invokes emacsclient to send a message to Emacs.

        The message is only sent is this object is not inactivated.
        """
        if self._active:
            self._log.debug('sending "%s"' % command)
            try:
                subprocess.call(
                    ['emacsclient', '-e', command], stdout=subprocess.PIPE)
            except OSError, e:
                self._log.debug('%s"' % e)


class EmacsServer(object):
    """Listener for Emacs notifications.

    When started by the EmacsEmbed object, the EMACS_SCRIPT is provided to
    Emacs to register some callbacks and create a link with Pida.
    EmacsServer is the server part of this link.
    """
    
    def __init__(self, cb):
        """Constructor."""
        self._log = logging.getLogger('emacs')
        self._cb = cb
        self._socket = None

    def connect(self):
        """Install the link between Pida and Emacs."""
        result = self._socket is not None
        if not result:
            try:
                self._socket = self._wait_connection()
                gobject.io_add_watch(self._socket, gobject.IO_IN |
                                     gobject.IO_HUP, self._cb_socket_event)
                result = True
            except socket.error, e:
                if e.args[0] == 111:
                    self._log.warn('emacs disconnected')
        return result
    
    def _wait_connection(self):
        """Wait for connection from Emacs."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 5001))
        s.listen(1)
        conn, addr = s.accept()
        self._log.debug('connection from "%s:%d"' % addr)
        return conn

    def _cb_socket_event(self, sock, condition):
        """Wait for Pida events.

        Called by GTK main loop as soon as Emacs notifies an event. This
        method also monitors the link with Emacs.

        Return True as long as Emacs is still alive.
        """
        cont = True
        if condition == gobject.IO_IN:
            data = sock.recv(1024)
            events = data.split('\n')
            for event in events:
                if event:
                    cont = self._cb_socket_read(event)
                
        elif condition == gobject.IO_HUP:
            self._log.warn('event: emacs disconnected')
            cont = False
            
        elif condition == gobject.IO_ERR:
            self._log.warn('event: io error')

        return cont

    def _cb_socket_read(self, data):
        """Analyse Emacs notifications and forward events to Pida.

        All Emacs notifications are composed of a message name, and possibly
        an argument. The EmacsServer object build the name of a related
        callback in the EmacsCallback object by prefixing the message name
        with 'cb_'.

        Return True as long as the link with Emacs should be maintained.
        """
        cont = True
        hook, args = data, ''
        sep = data.find(' ')
        if sep != -1:
            hook, args = data[0:sep], data[sep + 1:]
        name = 'cb_' + hook.replace('-', '_')
        if args.endswith('\n'):
            args = args[:-1]
        cb = getattr(self._cb.__class__, name, None)
        if callable(cb):
            cont = cb(self._cb, args)
        else:
            self._log.warn('unknown hook "%s"' % hook)
        return cont



EMACS_SCRIPT = """;; Emacs client script for Pida.
;; David Soulayrol <david.soulayrol@anciens.enib.fr>
;;
;; This script is automatically generated by pida when destroyed.
;; Leave untouched or modify it at your own risk.

(defconst pida-connection-terminator "\n"
  "The terminator used to send notifications to pida")

(defconst pida-connection-port 5001
  "The port used to communicate with pida")

(defvar pida-connection nil
  "The socket to comunicate with pida")


;; open-network-stream name buffer-or-name host service
(setq pida-connection 
      (open-network-stream "pida-connection" nil "localhost" pida-connection-port))
(process-kill-without-query pida-connection nil)

(defun pida-send-message (message)
  (process-send-string "pida-connection"
		       (concat message pida-connection-terminator)))
  
;; hook to the events pida is interested in.
(add-hook 
 'find-file-hooks
 '(lambda () 
    (pida-send-message (concat "find-file-hooks " buffer-file-name))))

(add-hook 
 'after-save-hook
 '(lambda () 
    (pida-send-message (concat "after-save-hook " buffer-file-name))))

(add-hook
 'kill-buffer-hook 
 '(lambda ()
    (pida-send-message (concat "kill-buffer-hook " buffer-file-name))))

(add-hook
 'window-configuration-change-hook
 '(lambda ()
    (pida-send-message (concat "window-configuration-change-hook " buffer-file-name))))

(add-hook
 'kill-emacs-hook
 '(lambda ()
    (pida-send-message "kill-emacs-hook")
    (delete-process pida-connection)))

;; <d_rol> is there a way to prevent emacs from showing the "GNU Emacs"
;;         first buffer ?
;; <pgas> d_rol: M-x customize-variable RET inhibit-splash-screen RET
(setq inhibit-splash-screen 1)
"""


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
