

# PIDA Imports
from pida.core.interfaces import IOptions, IEvents, ICommands, IActions, IFeatures
from pida.core.plugins import Registry
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import ActionsConfig
from pida.core.commands import CommandsConfig
from pida.core.features import FeaturesConfig


class Service(object):
    """Base Service Class"""

    options_config = OptionsConfig
    events_config = EventsConfig
    commands_config = CommandsConfig
    features_config = FeaturesConfig
    actions_config = ActionsConfig

    def __init__(self, boss=None):
        self.boss = boss
        self.log_debug('Loading Service')
        self.reg = Registry()

    def create_all(self):
        self.log_debug('Creating Service')
        self._register_options_config(self.options_config)
        self._register_events_config(self.events_config)
        self._register_commands_config(self.commands_config)
        self._register_feature_config(self.features_config)
        self._register_actions_config(self.actions_config)

    def subscribe_all(self):
        self.log_debug('Subscribing Service')
        self._subscribe_foreign_events()
        self._subscribe_foreign_features()
        self._subscribe_keyboard_shortcuts()

    def get_name(self):
        return self.servicename

    def pre_start(self):
        """Override to pre start up"""

    def start(self):
        """Override for main phase of startup"""

    ##########
    # Options

    def _register_options_config(self, config_cls):
        self.reg.register_plugin(
            instance=config_cls(self),
            singletons=(IOptions,)
        )

    # Public Options API
    def _get_options(self):
        return self.reg.get_singleton(IOptions)

    def get_option(self, name):
        return self._get_options().get_option(name)

    def opt(self, name):
        return self._get_options().get_value(name)

    ##########
    # Commands

    def _register_commands_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(ICommands,)
        )

    # Public Commands API

    def _get_commands(self):
        return self.reg.get_singleton(ICommands)

    def cmd(self, name, *args, **kw):
        if args:
            raise TypeError('You must call command %s in service %s with '
            'named arguments' % (name, self.get_name()))
        else:
            return self._get_commands().call(name, **kw)

    ##########
    # Events

    # Private Events API
    def _register_events_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IEvents,)
        )

    def _subscribe_foreign_events(self):
        self._get_events().subscribe_foreign_events()

    # Public Events API
    def _get_events(self):
        return self.reg.get_singleton(IEvents)

    def get_event(self, name):
        return self._get_events().get(name)

    def subscribe_foreign_event(self, servicename, name, callback):
        self.boss.subscribe_event(servicename, name, callback)

    def subscribe_event(self, name, callback):
        self._get_events().subscribe_event(name, callback)

    def emit(self, name, **kw):
        self._get_events().emit(name, **kw)

    ##########
    # Features

    def _register_feature_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IFeatures,)
        )

    def _subscribe_foreign_features(self):
        self._get_features().subscribe_foreign_features()

    def _get_features(self):
        return self.reg.get_singleton(IFeatures)

    # Public Feature API

    def list_features(self):
        return self._get_features().list_features()

    def subscribe_feature(self, feature, instance):
        self._get_features().subscribe_feature(feature, instance)

    def subscribe_foreign_feature(self, servicename, feature, instance):
        self.boss.subscribe_feature(servicename, feature, instance)

    def features(self, name):
        return self._get_features().get_feature_providers(name)

    ##########
    # Actions

    def _register_actions_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IActions,)
        )

    def _subscribe_keyboard_shortcuts(self):
        self._get_actions().subscribe_keyboard_shortcuts()

    def _get_actions(self):
        return self.reg.get_singleton(IActions)

    def get_action(self, name):
        return self._get_actions().get_action(name)

    def get_keyboard_options(self):
        return self._get_actions().get_keyboard_options()

    # Logging

    def log_debug(self, message):
        self.boss.log.debug('svc: %s: %s' % (self.get_name(), message))

    def log_info(self, message):
        self.boss.log.info('svc: %s: %s' % (self.get_name(), message))

    def log_warn(self, message):
        self.boss.log.warn('svc: %s: %s' % (self.get_name(), message))

    def log_error(self, message):
        self.boss.log.error('svc: %s: %s' % (self.get_name(), message))

