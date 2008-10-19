# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
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
