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

import os

from pida.core.pdbus import DbusConfig, SIGNAL, EXPORT, BUS, DBUS_NS
# PIDA Imports
from pida.core.service import Service
from pida.core.environment import session_name

from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

class RpcDbus(DbusConfig):
    
    def __init__(self, *args, **kwargs):
        super(RpcDbus, self).__init__(*args, **kwargs)

        if BUS is None:
            return
            
        BUS.add_signal_receiver(self.on_ping, 'PING_PIDA_INSTANCE', 
                                DBUS_NS())
        BUS.add_signal_receiver(self.on_ping_ext, 'PING_PIDA_INSTANCE_EXT', 
                                DBUS_NS())
        BUS.add_signal_receiver(self.on_ping_session, 'PING_PIDA_SESSION', 
                                DBUS_NS())

    @EXPORT(out_signature="i")
    def get_pid(self):
        return os.getpid()

    @EXPORT()
    def focus_window(self):
        self.svc.boss.window.present()

    @EXPORT(in_signature="b")
    def kill(self, force=False):
        self.svc.boss.stop(force)

    def on_ping_session(self, session):
        if session == session_name():
            self.on_ping()

    def on_ping(self):
        self.PONG_PIDA_INSTANCE(BUS.get_unique_name())

    def on_ping_ext(self):
        self.PONG_PIDA_INSTANCE_EXT(
            BUS.get_unique_name(),
            os.getpid(),
            session_name(),
            self.svc.boss.get_service('project').get_project_name() or '',
            len(self.svc.boss.get_service('buffer').get_documents())
            )

    @SIGNAL(signature="s")
    def PONG_PIDA_INSTANCE(self, uid):
        pass


    @SIGNAL(signature="sissi")
    def PONG_PIDA_INSTANCE_EXT(self, uid, pid, session, project, opened_files):
        pass

# Service class
class Rpc(Service):
    """DBus RPC Service""" 

    dbus_config = RpcDbus

    def start(self):
        if not BUS:
            self.boss.get_service('notify').notify(
                _('DBus python bindings are missing. Limited functionality.'),
                title=_('Modules missing'))

# Required Service attribute for service loading
Service = Rpc



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
