# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os
import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig
from pida.core.options import OptionsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.core.pdbus import DbusConfig, SIGNAL, EXPORT, BUS, DBUS_NS
from pida.core.environment import workspace_name

# locale
from pida.core.locale import Locale
locale = Locale('appcontroller')
_ = locale.gettext


LEXPORT = EXPORT(suffix='appcontroller')
LSIGNAL = SIGNAL(suffix='appcontroller')


class AppcontrollerConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
            'open_workspace_manager',
            _('Always show workspace manager'),
            bool,
            False,
            _('Always open the workspace manager when no workspace name is given'),
        )

class AppcontrollerActions(ActionsConfig):

    dbus_no_activate = ('quit_pida',)

    def create_actions(self):
        self.create_action(
            'quit_pida',
            TYPE_NORMAL,
            _('Quit PIDA'),
            _('Exit the application'),
            gtk.STOCK_QUIT,
            self.on_quit_pida,
            '<Control><Alt>q'
        )

    def on_quit_pida(self, action):
        self.svc.boss.stop()

class ApplicationDbus(DbusConfig):

    def __init__(self, *args, **kwargs):
        super(ApplicationDbus, self).__init__(*args, **kwargs)

        if BUS is None:
            return

        BUS.add_signal_receiver(self.on_ping, 'PING_PIDA_INSTANCE', 
                                DBUS_NS('appcontroller'))
        BUS.add_signal_receiver(self.on_ping_ext, 'PING_PIDA_INSTANCE_EXT', 
                                DBUS_NS('appcontroller'))
        BUS.add_signal_receiver(self.on_ping_workspace, 'PING_PIDA_WORKSPACE', 
                                DBUS_NS('appcontroller'))

    @LEXPORT(out_signature="i")
    def get_pid(self):
        return os.getpid()


    @LEXPORT(out_signature='s')
    def get_workspace_name(self):
        return workspace_name()

    @LEXPORT()
    def focus_window(self):
        self.svc.boss.window.present()

    @LEXPORT(in_signature="b")
    def kill(self, force=False):
        self.svc.boss.stop(force)

    def on_ping_workspace(self, workspace):
        if workspace == workspace_name():
            self.on_ping()

    def on_ping(self):
        self.PONG_PIDA_INSTANCE(BUS.get_unique_name())

    def on_ping_ext(self):
        self.PONG_PIDA_INSTANCE_EXT(
            BUS.get_unique_name(),
            os.getpid(),
            workspace_name(),
            self.svc.boss.get_service('project').get_project_name() or '',
            len(self.svc.boss.get_service('buffer').get_documents())
            )

    @LSIGNAL(signature="s")
    def PONG_PIDA_INSTANCE(self, uid):
        pass


    @LSIGNAL(signature="sissi")
    def PONG_PIDA_INSTANCE_EXT(self, uid, pid, workspace, project, opened_files):
        pass

    @LSIGNAL(signature="sissi")
    def PONG_PIDA_INSTANCE_EXT(self, uid, pid, workspace, project, opened_files):
        pass

    @LSIGNAL(signature="sis")
    def PIDA_START(self, uid, pid, workspace):
        pass

    @LSIGNAL(signature="sis")
    def PIDA_PRE_START(self, uid, pid, workspace):
        pass

    @LSIGNAL(signature="si")
    def PIDA_STOP(self, uid, pid):
        pass

    @LSIGNAL(signature="si")
    def PIDA_PRE_STOP(self, uid, pid):
        pass


# Service class
class Appcontroller(Service):
    """Main Application controller""" 

    actions_config = AppcontrollerActions
    options_config = AppcontrollerConfig
    dbus_config = ApplicationDbus

    label = _("Application")

    def start(self):
        if BUS is None:
            self.boss.get_service('notify').notify(
                _('DBus python bindings are missing. Limited functionality.'),
                title=_('Modules missing'))
        else:
            self.dbus.PIDA_START(
                BUS.get_unique_name(),
                os.getpid(),
                workspace_name()
            )

    def pre_start(self):
        if BUS is not None:
            self.dbus.PIDA_PRE_START(
                BUS.get_unique_name(),
                os.getpid(),
                workspace_name()
            )
        return True

    def pre_stop(self):
        if BUS is not None:
            self.dbus.PIDA_PRE_STOP(
                BUS.get_unique_name(),
                os.getpid()
            )
        return True

    def stop(self):
        if BUS is not None:
            self.dbus.PIDA_STOP(
                BUS.get_unique_name(),
                os.getpid()
            )
        return True


# Required Service attribute for service loading
Service = Appcontroller



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
