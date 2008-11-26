# -*- coding: utf-8 -*-
"""
    2-way communication with emacs
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Communication with Emacs process is handled by EmacsClient in the pIDA->Emacs
    way, and EmacsServer the other way. On occurence of a message, EmacsServer
    extracts a request name and arguments, and then tries to invoke the matching
    method on a EmacsCallback object (see editor/emacs/emacs.py).
  
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import logging
import os
import pwd
import socket
import subprocess
import threading

import gobject


class EmacsClient(object):
    """Tool for sending orders to emacs.

    EmacsClient class relies on the emacsclient binary.
    Note that this utility works with a server started from inside a running
    emacs instance. We assume for now that the emacs instance running in pida
    is the only one having a running server.
    """
    
    def __init__(self, instance_id, svc):
        """Constructor."""
        self._log = logging.getLogger('emacs')
        self._active = True
        self._instance_id = instance_id
        self._socket_path = _get_socket_path(self._instance_id)
        self._pending_commands = []
        self._svc = svc

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
        self._send('(pida-save-buffer "%s")' % self._svc.current_document.filename)

    def save_buffer_as(self, filename):
        self._send('(pida-save-buffer-as "%s" "%s"))' % (self._svc.current_document.filename, filename))

    def close_buffer(self, buffer):
        self._send('(kill-buffer (get-file-buffer "%s"))' % buffer)

    def frame_setup(self):
        self._send('(pida-frame-setup nil)')

    def cut(self):
        self._send('(pida-cut "%s")' % self._svc.current_document.filename)

    def copy(self):
        self._send('(pida-copy "%s")' % self._svc.current_document.filename)

    def paste(self):
        self._send('(pida-paste "%s")' % self._svc.current_document.filename)

    def goto_line(self, line):
        self._send('(pida-goto-line "%s" %s)' % (self._svc.current_document.filename, line))

    def revert_buffer(self):
        self._send('(revert-buffer)')

    def undo(self):
        self._send('(undo-only)')

    def redo(self):
        # Well... I'm still a bit disturbed with the undo / redo of Emacs
        self._send('(undo)')

    def quit(self):
        self._send('(pida-quit)')

    def _send(self, command):
        """Invokes emacsclient to send a message to Emacs.

        The message is only sent is this object is not inactivated.
        """
        # The implementation here is still broken: if communnication
        # fails once, then the failed command is not tried again until
        # another command is issued... (by experience, this is not a
        # problem so far)
        #
        # Another problem is the use of emacs-client which should be bypassed.
        if self._active:
            self._log.debug('queuing "%s"' % command)
            self._pending_commands.append(command)
            if os.path.exists(self._socket_path):
                try:
                    while len(self._pending_commands):
                        cmd = self._pending_commands[0]
                        self._log.debug('calling "%s"' % cmd)
                        subprocess.call(
                            ['emacsclient', '-s', self._instance_id, '-e', cmd],
                            stdout=subprocess.PIPE)
                        self._pending_commands.pop(0)
                except OSError, e:
                    self._log.error('%s' % e)
            else:
                self._log.debug('socket not ready')

class EmacsServer(object):
    """Listener for Emacs notifications.

    When started by the EmacsEmbed object, the EMACS_SCRIPT is provided to
    Emacs to register some callbacks and create a link with Pida.
    EmacsServer is the server part of this link.
    """

    # The first port tried to bind.
    # The author believes you could read it 'pida'.
    BASE_PORT = 9164
    
    def __init__(self, cb):
        """Constructor."""
        self._log = logging.getLogger('emacs')
        self._cb = cb
        self._socket_listen = None
        self._socket = None

    def bind(self):
        """Bind the listening socket and return the elected port."""
        port = EmacsServer.BASE_PORT
        bound = False
        self._socket_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not bound: 
            try:
                self._socket_listen.bind(('', port))
                bound = True
            except socket.error:
                port += 1
        self._socket_listen.listen(1)
        threading.Thread(name='emacs listener', target=self._wait_connection).start()
        return port

    def _wait_connection(self):
        """Wait for connection from Emacs."""
        self._socket, addr = self._socket_listen.accept()
        self._log.debug('connection from "%s:%d"' % addr)
        try:
            gobject.io_add_watch(self._socket, gobject.IO_IN |
                                 gobject.IO_HUP, self._cb_socket_event)
            result = True
        except socket.error, e:
            if e.args[0] == 111:
                self._log.warn('emacs disconnected')

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


def _get_socket_path(instance_id):
    # Only tested on unix until now.
    uid = pwd.getpwnam(os.environ['USER']).pw_uid
    dirname = os.path.join("/tmp", "emacs%s" % uid)
#     if not os.path.exists(dirname):
#         os.makedirs(dirname)
#         os.chmod(dirname, 0700)
#         os.chown(dirname, uid, uid)

    return os.path.join(dirname, instance_id)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
