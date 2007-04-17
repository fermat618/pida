import gtk

from pida.core.servicemanager import ServiceManager 
from pida.core.log import build_logger

from pida.ui.window import PidaWindow

class Boss(object):


    def __init__(self, env=None):
        self._env = env
        self.log = build_logger('pida')
        self._sm = ServiceManager(self)
        self._window = PidaWindow(self)

    def start(self):
        self._activate_services()
        self._activate_editor()
        self._window.start()
        self._start_services()
        self._start_editor()

    def stop(self):
        pass

    def loop_ui(self):
        gtk.main()
        #self._window.show_and_loop()

    def _activate_services(self):
        self._sm.activate_services()

    def _activate_editor(self):
        editor_name = self.get_service('editor').opt('editor_type')
        self._sm.activate_editor(editor_name)

    def _start_services(self):
        self._sm.start_services()

    def _start_editor(self):
        self._sm.start_editor()

    def get_service(self, servicename):
        return self._sm.get_service(servicename)

    def get_services(self):
        return self._sm.get_services()

    def get_service_dirs(self):
        if self._env is None:
            return []
        else:
            return [
                self._env.get_base_service_directory()
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

    def subscribe_event(self, servicename, event, callback):
        svc = self.get_service(servicename)
        svc.subscribe_event(event, callback)

    def subscribe_feature(self, servicename, feature, instance):
        svc = self.get_service(servicename)
        svc.subscribe_feature(feature, instance)

    def add_action_group_and_ui(self, actiongroup, uidef):
        self._window.add_action_group(actiongroup)
        self._window.add_uidef(uidef)

    def cmd(self, servicename, commandname, **kw):
        return self.get_service(servicename).cmd(commandname, **kw)

    def addd_view(self, bookname, view, present=False):
        self._window.add_view(bookname, view, present)

    def remove_view(self, view):
        self._window.remove_view(view)

    def detach_view(self, view):
        self._window.detach_view(view)

    def get_pida_home(self):
        return self._env.pida_home

    def get_window(self):
        return self._window
    window = property(get_window)

