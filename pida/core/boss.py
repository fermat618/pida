

from pida.core.servicemanager import ServiceManager

from pida.ui.window import PidaWindow

class Boss(object):


    def __init__(self, env=None):
        self._env = env
        self._sm = ServiceManager(self)
        self._window = PidaWindow(self)

    def start(self):
        self._load_services()
        self._create_services()
        self._subscribe_services()
        self._start_services()
        self._window.start()

    def stop(self):
        pass

    def loop_ui(self):
        self._window.show_and_loop()

    def _load_services(self):
        self._sm.load_services()

    def _create_services(self):
        self._sm.create_all()

    def _subscribe_services(self):
        self._sm.subscribe_all()

    def _start_services(self):
        self._sm.start_all()

    def get_service(self, servicename):
        return self._sm.get_service(servicename)

    def get_services(self):
        return self._sm.get_services()

    def get_service_dirs(self):
        if self._env is None:
            return []
        else:
            return [self._env.get_base_service_directory()]


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
        self.get_service(servicename).cmd(commandname, **kw)

    def add_view(self, bookname, view):
        self._window.add_view(bookname, view)

