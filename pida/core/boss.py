# -*- coding: utf-8 -*-
"""
    pida.core.boss
    ~~~~~~~~~~~~~~

    Boss is the main controller for Pida,
    it manages glueing together the rest

    :license: GPL2 or later
    :copyright: 2005-2008 by The PIDA Project
"""

import gtk
import os
import sys
import pida

from pida.core.environment import (is_firstrun, firstrun_filename)
from pida.core.servicemanager import ServiceManager, ServiceModuleError
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
        self._sm = ServiceManager(self,
                                  update_progress=self._splash.update_progress)
        self._run_first_time()
        self.window = PidaWindow(self)

    def check_editor(self, editor_name):
        """
        Check if the current editor passes the sanity check

        :returns new editor name
        """
        try:
            editor = self._sm.get_editor(editor_name)
            if editor.get_sanity_errors():
                return self._run_first_time(True)
        except ServiceModuleError:
            return self._run_first_time(True)
        return editor_name

    def _run_first_time(self, force=False):
        if is_firstrun() or force:
            from pida.utils.firstrun import FirstTimeWindow
            ft = FirstTimeWindow(self._sm.get_available_editors())
            success, editor = ft.run(firstrun_filename)
            self.override_editor = editor
            self.quit_before_started = not success
            return editor
        else:
            self.override_editor = None
            self.quit_before_started = False

    def start(self):
        if self.quit_before_started:
            sys.exit() #XXX: errors?
            raise RuntimeError('quit_before_started was set #XXX: better error')
        else:
            self._icons = IconRegister()
            self._icons.register_file_icons_for_directory(
                os.path.abspath(os.path.join(
                    pida.__path__[0],
                    'resources/pixmaps'
                )))
            self._sm.activate_services()
            if self.override_editor is not None:
                self.get_service('editor').set_opt('editor_type',
                    self.override_editor)
            editor_name = self.get_service('editor').opt('editor_type')
            editor_name = self.check_editor(editor_name)
            self._sm.activate_editor(editor_name)
            self.window.start()
            self._sm.start_services()
            self._sm.start_editor()

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
        try:
            gtk.main()
        except KeyboardInterrupt:
            sys.exit(1)

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

    def add_action_group_and_ui(self, actiongroup, package, path):
        self.window.add_action_group(actiongroup)
        return self.window.add_uidef(package, path)

    def remove_action_group_and_ui(self, actiongroup, ui_merge_id):
        self.window.remove_uidef(ui_merge_id)
        self.window.remove_action_group(actiongroup)

    def cmd(self, servicename, commandname, **kw):
        return self.get_service(servicename).cmd(commandname, **kw)

    def show_splash(self):
        self._splash = SplashScreen()
        self._splash.show_splash()

    def hide_splash(self):
        if not hasattr(self, "_splash"):
            return
        self._sm.update_progress = None
        self._splash.hide_splash()
        del self._splash

