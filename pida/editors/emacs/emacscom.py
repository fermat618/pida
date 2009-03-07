# -*- coding: utf-8 -*-
"""
    communication with emacs using dbus
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2005-2009 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import time
from pida.core.log import get_logger

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    MAINLOOP = DBusGMainLoop(set_as_default=True)
except ImportError:
    pass

class EmacsClient(object):
    
    def __init__(self, callback, svc):
        self._log = get_logger('emacs')
        self._callback = callback
        self._svc = svc
        session = dbus.SessionBus()
        proxy = None
        namespace = '.'.join(['uk.co.pida.Emacs', 
                       os.environ["PIDA_DBUS_UUID"]])
        while proxy is None:
            try:
                proxy = session.get_object(namespace, '/uk/co/pida/Emacs')
            except dbus.DBusException:
                proxy = None
                time.sleep(0.2)
        self.proxy = proxy

    def connect_signals(self):
        """
        Register dbus signals from emacs
        """
        for evt in ['BufferOpen', 'BufferClose', 'BufferSave', 
                    'BufferChange', 'EmacsKill']:
            self.proxy.connect_to_signal(evt, 
                                         getattr(self._callback, 
                                                 'em_%s' % evt),
                                         dbus_interface=
                                         "uk.co.pida.Emacs")
        self.frame_setup()

    def quit(self):
        """
        Quit pida - notify emacs
        """
        self._log.debug('Stop Emacs')
        self.proxy.StopEmacs(reply_handler=lambda *a: None,
                             error_handler=lambda *a: None,
                             dbus_interface="uk.co.pida.Emacs")

    def open_file(self, file_name):
        self._log.debug('Open File %s'% file_name)
        self.proxy.OpenFile(file_name, dbus_interface="uk.co.pida.Emacs")

    def change_buffer(self, file_name):
        self._log.debug('Change Buffer to %s' % file_name)
        self.proxy.ChangeBuffer(file_name, dbus_interface="uk.co.pida.Emacs")

    def close_buffer(self, file_name):
        self._log.debug('Close Buffer for %s' % file_name)
        self.proxy.CloseBuffer(file_name, dbus_interface="uk.co.pida.Emacs")

    def save_buffer(self):
        self._log.debug('Save Buffer %s' % self._svc.current_document.filename)
        self.proxy.SaveBuffer(self._svc.current_document.filename, 
                              dbus_interface="uk.co.pida.Emacs")

    def cut(self):
        self._log.debug('Cut')
        self.proxy.Cut(self._svc.current_document.filename, 
                       dbus_interface="uk.co.pida.Emacs")

    def copy(self):
        self._log.debug('Copy')
        self.proxy.Copy(self._svc.current_document.filename, 
                        dbus_interface="uk.co.pida.Emacs")

    def undo(self):
        self._log.debug('Undo')
        self.proxy.Undo(dbus_interface="uk.co.pida.Emacs")
        
    def redo(self):
        self._log.debug('No Redo - only reverse undo')

    def paste(self):
        self._log.debug('Paste')
        self.proxy.Paste(self._svc.current_document.filename, 
                         dbus_interface="uk.co.pida.Emacs")

    def goto_line(self, line):
        self._log.debug('Goto Line %s'% line)
        self.proxy.GotoLine(self._svc.current_document.filename, 
                            line, 
                            dbus_interface="uk.co.pida.Emacs")

    def frame_setup(self):
        self._log.debug('Setup the menu Bars')
        self.proxy.FrameSetup(None, dbus_interface="uk.co.pida.Emacs",
                              reply_handler=lambda *a: None,
                              error_handler=lambda *a: None)
    
    def set_directory(self, path):
        self._log.debug('Set Directory to %s' % path)
        self.proxy.SetDirectory(path, 
                                reply_handler=lambda *a: None,
                                error_handler=lambda *a: None, 
                                dbus_interface="uk.co.pida.Emacs")
        return None
        

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
