

from pida.core.servicemanager import ServiceManager

from pida.ui.window import PidaWindow

class Boss(object):


    def __init__(self, env=None):
        self._env = env
        self._sm = ServiceManager(self)
        self._window = PidaWindow(self)

    def start(self):
        self._load_services()
        self._start_services()
        self._subscribe_services()

    def stop(self):
        pass

    def loop_ui(self):
        self._window.show_and_loop()

    def _load_services(self):
        self._sm.load_services()

    def _start_services(self):
        self._sm.create_all()

    def _subscribe_services(self):
        self._sm.subscribe_all()

    def get_service(self, servicename):
        return self._sm.get_service(servicename)

    def get_services(self):
        return self._sm.get_services()

    def get_service_dirs(self):
        return []

    def subscribe_event(self, servicename, event, callback):
        svc = self.get_service(servicename)
        svc.subscribe_event(event, callback)

    def subscribe_feature(self, servicename, feature, instance):
        svc = self.get_service(servicename)
        svc.subscribe_feature(feature, instance)

