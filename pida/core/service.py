
from pida.core.interfaces import IOptionsConfig
from pida.core.plugins import Registry
from pida.core.options import OptionsConfig


class Service(object):
    """Base Service Class"""

    options_config = OptionsConfig

    def __init__(self, boss=None):
        self.boss = boss
        self.reg = Registry()
        self._register_all_config()

    def _register_all_config(self):
        self._register_options_config(self.options_config)

    def _register_options_config(self, config_cls):
        self.reg.register_plugin(
            instance=config_cls(self),
            singletons=(IOptionsConfig,)
        )

    # Public Options API
    def get_options(self):
        return self.reg.get_singleton(IOptionsConfig)

    def get_option(self, name):
        return self.get_options().get_option(name)

    def opt(self, name):
        return self.get_option(name).value



