
from pida.core.interfaces import IOptions, IEvents, ICommands
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

    def create_all(self):
        self._register_options_config(self.options_config)
        self._register_events_config(self.events_config)

    def subscribe_all(self):
        self._subscribe_foreign_events()

    ##########
    # Options

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
    # Commands

    def _register_commands_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(ICommands,)
        )

    # Public Commands API

    def get_commands(self):
        return self.reg.get_singleton(ICommands)

    ##########
    # Events

    # Private Events API
    def _register_events_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IEvents,)
        )

    def _subscribe_foreign_events(self):
        self.get_events().subscribe_foreign_events()

    # Public Events API
    def get_events(self):
        return self.reg.get_singleton(IEvents)

    def get_event(self, name):
        return self.get_events().get(name)

    def subscribe_foreign_event(self, servicename, name, callback):
        self.boss.subscribe_event(servicename, name, callback)

    def subscribe_event(self, name, callback):
        self.get_events().subscribe_event(name, callback)

    def emit(self, name):
        self.get_events().emit(name)


