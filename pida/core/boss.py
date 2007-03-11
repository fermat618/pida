
from pida.core.plugins import Registry
from pida.core.interfaces import IService


class Boss(object):

    # temporary
    service_dirs = ['/home/ali/tmp']

    def __init__(self, env=None):
        self._env = env
        self._reg = Registry()

    def start(self):
        pass

    def stop(self):
        pass

    def register_service(self, service):
        self._reg.register_plugin(
            instance=service,
            singletons=(
                service.servicename,
            ),
            features=(
                IService,
            )
        )
        print service
