
from pida.core.interfaces import IOptions, IEvents
from pida.core.plugins import Registry
from pida.core.options import OptionsConfig
from pida.core.events import EventsConfig


class Service(object):
    """Base Service Class"""

    options_config = OptionsConfig
    events_config = EventsConfig

    def __init__(self, boss=None):
        self.boss = boss
        self.reg = Registry()
        self._register_all_config()

    def _register_all_config(self):
        self._register_options_config(self.options_config)
        self._register_events_config(self.events_config)

    def _register_options_config(self, config_cls):
        self.reg.register_plugin(
            instance=config_cls(self),
            singletons=(IOptions,)
        )

    # Public Options API
    def get_options(self):
        return self.reg.get_singleton(IOptions)

    def get_option(self, name):
        return self.get_options().get_option(name)

    def opt(self, name):
        return self.get_option(name).value

    ##########
    # Events

    # Private Events API
    def _register_events_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IEvents,)
        )

    # Public Events API
    def get_events(self):
        return self.reg.get_singleton(IEvents)

    def get_event(self, name):
        return self.get_events().get(name)

    def emit(self, name):
        self.get_events().emit(name)


