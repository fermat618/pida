
from pida.core.plugins import Registry


class Boss(object):

    def __init__(self, env=None):
        self._env = env
        self._reg = Registry()

    def start(self):
        pass

    def stop(self):
        pass

    def _load_plugins(self):
        pass
