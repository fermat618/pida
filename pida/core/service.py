"""
PIDA Services
"""

# PIDA Imports
from pida.core.interfaces import IOptions, IEvents, ICommands, IActions, IFeatures
from pida.core.plugins import Registry
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import ActionsConfig
from pida.core.commands import CommandsConfig
from pida.core.features import FeaturesConfig
from pida.core.log import get_logger
from pida.utils.descriptors import cached_property

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class Service(object):
    """Base Service Class"""

    label = None

    options_config = OptionsConfig
    events_config = EventsConfig
    commands_config = CommandsConfig
    features_config = FeaturesConfig
    actions_config = ActionsConfig

    def __init__(self, boss):
        self.boss = boss
        self.log.debug('Loading Service')
        self.reg = Registry()

    def create_all(self):
        """
        Called to create all the services by the
        {servicemanager.ServiceManager}
        """

        self._register_options_config(self.options_config)
        self._register_events_config(self.events_config)
        self._register_commands_config(self.commands_config)
        self._register_feature_config(self.features_config)
        self._register_actions_config(self.actions_config)

    def subscribe_all(self):
        self._subscribe_foreign_events()
        self._subscribe_foreign_features()
        self._subscribe_keyboard_shortcuts()

    @classmethod
    def get_name(cls):
        return cls.__module__.split('.')[-1]

    @staticmethod
    def sort_key(service): #XXX: for service sorting
        return service.get_name()

    @classmethod
    def get_label(cls):
        return cls.label or cls.get_name().capitalize()

    def pre_start(self):
        """Override to pre start up"""

    def start(self):
        """Override for main phase of startup"""

    def stop(self):
        """Override to stop service"""

    def stop_components(self):
        # Will remove everything
        self._unsubscribe_foreign_events()
        self._unsubscribe_foreign_features()
        self._unregister_actions_config()

    ##########
    # Options

    def _register_options_config(self, config_cls):
        instance = config_cls(self)
        self.reg.register_plugin(
            instance=instance,
            singletons=(IOptions,)
        )

    # Public Options API
    def get_options(self):
        return self.reg.get_singleton(IOptions)

    def get_option(self, name):
        return self.get_options().get_option(name)

    def opt(self, name):
        return self.get_options().get_value(name)

    def set_opt(self, name, value):
        return self.get_options().set_value(name, value)

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

    def cmd(self, commandname, *args, **kw):
        if args:
            raise TypeError(
                    _('You must call command %(cmd)s in service %(svc)s with named arguments')
                    % {'cmd':commandname, 'svc':self.get_name()})
        else:
            return self._get_commands().call(commandname, **kw)

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

    def _unsubscribe_foreign_events(self):
        self._get_events().unsubscribe_foreign_events()

    # Public Events API
    def _get_events(self):
        return self.reg.get_singleton(IEvents)

    def get_event(self, name):
        return self._get_events().get(name)

    def subscribe_foreign_event(self, servicename, name, callback):
        self.boss.subscribe_event(servicename, name, callback)

    def unsubscribe_foreign_event(self, servicename, name, callback):
        self.boss.unsubscribe_event(servicename, name, callback)

    def subscribe_event(self, name, callback):
        self._get_events().subscribe_event(name, callback)

    def unsubscribe_event(self, name, callback):
        self._get_events().unsubscribe_event(name, callback)
        

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

    def _unsubscribe_foreign_features(self):
        self._get_features().unsubscribe_foreign_features()

    def _get_features(self):
        return self.reg.get_singleton(IFeatures)

    # Public Feature API

    def list_features(self):
        return self._get_features().list_features()

    def has_foreign_feature(self, servicename, featurename):
        return self._get_features().has_foreign_feature(servicename, featurename)

    def subscribe_feature(self, feature, instance):
        return self._get_features().subscribe_feature(feature, instance)

    def unsubscribe_feature(self, feature_object):
        self._get_features().unsubscribe_feature(feature_object)

    def subscribe_foreign_feature(self, servicename, feature, instance):
        return self.boss.subscribe_feature(servicename, feature, instance)

    def unsubscribe_foreign_feature(self, servicename, feature_object):
        self.boss.unsubscribe_feature(servicename, feature_object)

    def features(self, name):
        return self._get_features().get_feature_providers(name)

    ##########
    # Actions

    def _register_actions_config(self, config_cls):
        self.reg.register_plugin(
            instance = config_cls(self),
            singletons=(IActions,)
        )

    def _unregister_actions_config(self):
        self._get_actions().remove_actions()

    def _subscribe_keyboard_shortcuts(self):
        self._get_actions().subscribe_keyboard_shortcuts()

    def _get_actions(self):
        return self.reg.get_singleton(IActions)

    def get_action_group(self):
        return self._get_actions().get_action_group()

    def get_action(self, name):
        return self._get_actions().get_action(name)

    def get_keyboard_options(self):
        return self._get_actions().get_keyboard_options()

    # Logging

    @cached_property
    def log(self):
        return get_logger('pida.svc.' + self.get_name())


    # window proxy

    @property
    def window(self):
        return self.boss.window

    def save_dlg(self, *args, **kw):
        return self.window.save_dlg(*args, **kw)

    def open_dlg(self, *args, **kw):
        return self.window.open_dlg(*args, **kw)

    def info_dlg(self, *args, **kw):
        return self.window.info_dlg(*args, **kw)

    def error_dlg(self, *args, **kw):
        return self.window.error_dlg(*args, **kw)

    def yesno_dlg(self, *args, **kw):
        return self.window.yesno_dlg(*args, **kw)

    def error_list_dlg(self, msg, errs):
        return self.window.error_list_dlg('%s\n\n* %s' % (msg, '\n\n* '.join(errs)))


