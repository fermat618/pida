"""
    pida.core.boss
    ~~~~~~~~~~~~~~

    Boss is the main controller for Pida,
    it manages glueing together the rest

    :license: GPL2 or later
    :copyright:
        * 2007-2008 Ali Afshar
        * 2007-2008 Ronny Pfannschmidt
"""

import os
import gtk

from pida.core.environment import (is_firstrun, firstrun_filename, is_safe_mode,
    session_name)
from pida.core.servicemanager import ServiceManager
from pida.ui.icons import IconRegister
from pida.ui.window import PidaWindow
from pida.ui.splash import SplashScreen

from pida.core.pdbus import DbusConfig, SIGNAL, EXPORT
from pida.utils.pdbus import BUS, DBUS_NS

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class BossDbus(DbusConfig):
    
    def __init__(self, *args, **kwargs):
        super(BossDbus, self).__init__(*args, **kwargs)
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
        self.svc.window.present()

    @EXPORT(in_signature="b")
    def kill(self, force=False):
        self.svc.stop(force)

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
            self.svc.get_service('project').get_project_name() or '',
            len(self.svc.get_service('buffer').get_documents())
            )

    @SIGNAL(signature="s")
    def PONG_PIDA_INSTANCE(self, uid):
        pass


    @SIGNAL(signature="sissi")
    def PONG_PIDA_INSTANCE_EXT(self, uid, pid, session, project, opened_files):
        pass

class Boss(object):

    def __init__(self):
        self.show_splash()
        self.dbus = BossDbus(self)
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

    def stop(self, force=False):
        if force:
            gtk.main_quit()
        elif self.window.yesno_dlg(_('Are you sure you want to quit PIDA ?')):
            # This causes pida-quit to be called on our Emacs and causes
            # a clean shutdown.
            self._sm.stop()
            gtk.main_quit()
        else:
            return True

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

    def get_name(self):
        return "boss"

