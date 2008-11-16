# -*- coding: utf-8 -*-
"""
    pida.core.boss
    ~~~~~~~~~~~~~~

    Boss is the main controller for Pida,
    it manages glueing together the rest

    :license: GPL2 or later
    :copyright: 2005-2008 by The PIDA Project
"""

import os
import gtk

from pida.core.environment import (is_firstrun, firstrun_filename, is_safe_mode,
    workspace_name)
from .options import OptionsManager
from pida.core.servicemanager import ServiceManager
from pida.ui.icons import IconRegister
from pida.ui.window import PidaWindow
from pida.ui.splash import SplashScreen

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext



class Boss(object):

    def __init__(self):
        self.show_splash()
        self._sm = ServiceManager(self)
        self._run_first_time()
        self.window = PidaWindow(self)

    def _run_first_time(self):
        if is_firstrun():
            from pida.utils.firstrun import FirstTimeWindow
            ft = FirstTimeWindow(self._sm.get_available_editors())
            success, editor = ft.run(firstrun_filename)
            self.override_editor = editor
            self.quit_before_started = not success
        else:
            self.override_editor = None
            self.quit_before_started = False

    def start(self):
        if self.quit_before_started:
            return False
        else:
            self._sm.activate_services()
            if self.override_editor is not None:
                self.get_service('editor').set_opt('editor_type',
                    self.override_editor)
            editor_name = self.get_service('editor').opt('editor_type')
            self._sm.activate_editor(editor_name)
            self._icons = IconRegister()
            self.window.start()
            self._sm.start_services()
            self._sm.start_editor()
            return True

    def stop(self, force=False, kill=False):
        """
        Stop pida.
        @force: on True: doesn't ask the user to quite, but a service may ask 
                for actions. Services can't stop the shutdown process
        @kill: on True: kill pida hard, nothing is informed or saved
        """
        if kill:
            gtk.main_quit()
        if force:
            self._sm.stop(force=force)
            gtk.main_quit()
        elif self.window.yesno_dlg(_('Are you sure you want to quit PIDA ?')):
            # in non force mode we only kill ourself if service manager
            # returns True
            if self._sm.stop():
                gtk.main_quit()
        else:
            return False

    def loop_ui(self):
        gtk.main()

    def get_service(self, servicename):
        return self._sm.get_service(servicename)

    def get_services(self):
        return self._sm.get_services()

    @property
    def editor(self):
        return self._sm.editor

    def get_plugins(self):
        return self._sm.get_plugins()

    def start_plugin(self, name):
        return self._sm.start_plugin(name)

    def stop_plugin(self, name):
        return self._sm.stop_plugin(name)

    def add_action_group_and_ui(self, actiongroup, uidef):
        self.window.add_action_group(actiongroup)
        return self.window.add_uidef(uidef)

    def remove_action_group_and_ui(self, actiongroup, ui_merge_id):
        self.window.remove_uidef(ui_merge_id)
        self.window.remove_action_group(actiongroup)

    def cmd(self, servicename, commandname, **kw):
        return self.get_service(servicename).cmd(commandname, **kw)

    def show_splash(self):
        self._splash = SplashScreen()
        self._splash.show_splash()

    def hide_splash(self):
        self._splash.hide_splash()

