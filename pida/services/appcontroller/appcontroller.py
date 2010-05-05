# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os
import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.options import OptionsConfig
from pida.core.actions import ActionsConfig

from pida.core.pdbus import DbusConfig, SIGNAL, EXPORT, BUS, DBUS_NS
from pida.core.environment import workspace_name
from pida.utils.serialize import loads, dumps

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
            gtk.Action,
            _('Quit PIDA'),
            _('Exit the application'),
            gtk.STOCK_QUIT,
            self.on_quit_pida,
            '<Control><Alt>q'
        )

    def on_quit_pida(self, action):
        self.svc.boss.stop()

class ApplicationDbus(DbusConfig):


    @LEXPORT(in_signature='s', out_signature='s')
    def cmd(self, json_dump):
        data = loads(json_dump)
        result = self.svc.boss.cmd(
                data['service'],
                data['method'],
                **data['kwargs']
                )
        #XXX: error checking
        return dumps(result, indent=2)

    @LEXPORT(out_signature="i")
    def get_pid(self):
        return os.getpid()

    @LEXPORT(out_signature='s')
    def get_workspace_name(self):
        return workspace_name()

    @LEXPORT(out_signature='s')
    def get_instance_status(self):

        return dumps({
            'pid': os.getpid(),
            'workspace': workspace_name(),
            'buffers': self.svc.boss.cmd('buffer', 'get_buffer_names'),
            'project': getattr(
                self.svc.boss.cmd('project','get_current_project'),
                'name', ''),
            }, indent=2)

    @LEXPORT()
    def focus_window(self):
        self.svc.boss.window.present()

    @LEXPORT(in_signature="b")
    def kill(self, force=False):
        self.svc.boss.stop(force)

# Service class
class Appcontroller(Service):
    """Main Application controller""" 

    actions_config = AppcontrollerActions
    options_config = AppcontrollerConfig
    dbus_config = ApplicationDbus

    label = _("Application")

    def start(self):
        #XXX: remove ince we use execnet
        if BUS is None:
            self.boss.get_service('notify').notify(
                _('DBus python bindings are missing. '
                  'Please don\'t start multiple Instances.'),
                title=_('DBus Modules missing'))



# Required Service attribute for service loading
Service = Appcontroller



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
