import logging
import sys
import warnings
import gtk

from pida.core.servicemanager import ServiceManager
from pida.core.log import get_logger

from pida.ui.icons import IconRegister
from pida.ui.window import PidaWindow
from pida.ui.splash import SplashScreen

from pida.utils.firstrun import FirstTimeWindow

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

log = get_logger('pida')

class Boss(object):


    def __init__(self, env=None):
        self._env = env

        if env.is_debug():
            get_logger().setLevel(logging.DEBUG)
        else:
            get_logger().setLevel(logging.INFO)

        self.show_splash()
        self._sm = ServiceManager(self)
        self._run_first_time()
        self.window = PidaWindow(self)

    @property
    def log(self):
        warnings.warn("log is deprecated", DeprecationWarning, 2)
        return log

    def _run_first_time(self):
        if not self._env.has_firstrun() or self._env.is_firstrun():
            ft = FirstTimeWindow(self._sm.get_available_editors())
            success, editor = ft.run(self._env.get_firstrun_filename())
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
        else:
            return True

    def loop_ui(self):
        gtk.main()

    def get_service(self, servicename):
        return self._sm.get_service(servicename)

    def get_services(self):
        return self._sm.get_services()

    def get_service_dirs(self):
        if self._env is None:
            return []
        else:
            return [
                self._env.get_base_service_directory(),
                self._env.get_local_service_directory(),
            ]

    def get_editor_dirs(self):
        if self._env is None:
            return []
        else:
            return [
                self._env.get_base_editor_directory(),
            ]

    def get_editor(self):
        return self._sm.editor

    editor = property(get_editor)

    def get_plugins(self):
        return self._sm.get_plugins()

    def start_plugin(self, plugin_path):
        return self._sm.start_plugin(plugin_path)

    def stop_plugin(self, plugin_name):
        return self._sm.stop_plugin(plugin_name)


    def add_action_group_and_ui(self, actiongroup, uidef):
        self.window.add_action_group(actiongroup)
        return self.window.add_uidef(uidef)

    def remove_action_group_and_ui(self, actiongroup, ui_merge_id):
        self.window.remove_uidef(ui_merge_id)
        self.window.remove_action_group(actiongroup)

    def cmd(self, servicename, commandname, **kw):
        return self.get_service(servicename).cmd(commandname, **kw)

    def get_pida_home(self):
        return self._env.pida_home

    def show_splash(self):
        self._splash = SplashScreen()
        self._splash.show_splash()

    def hide_splash(self):
        self._splash.hide_splash()


