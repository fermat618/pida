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

    def create_all(self):
        """
        Called to create all the services by the
        {servicemanager.ServiceManager}
        """
        
        self.options = self.options_config(self)
        self.events = self.events_config(self)
        self.commands = self.commands_config(self)
        self.features = self.features_config(self)
        self.actions = self.actions_config(self)

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
    # Options API
    def get_option(self, name):
        return self.options.get_option(name)

    def opt(self, name):
        return self.options.get_value(name)

    def set_opt(self, name, value):
        return self.options.set_value(name, value)

    ##########
    # Commands API


    def cmd(self, commandname, **kw):
        return self.commands.call(commandname, **kw)

    ##########
    # Events

    # Private Events API

    def _subscribe_foreign_events(self):
        self.events.subscribe_foreign_events()

    def _unsubscribe_foreign_events(self):
        self.events.unsubscribe_foreign_events()

    # Public Events API
    def get_event(self, name):
        return self.events.get(name)

    def subscribe_foreign_event(self, servicename, name, callback):
        self.boss.subscribe_event(servicename, name, callback)

    def unsubscribe_foreign_event(self, servicename, name, callback):
        self.boss.unsubscribe_event(servicename, name, callback)

    def subscribe_event(self, name, callback):
        self.events.subscribe_event(name, callback)

    def unsubscribe_event(self, name, callback):
        self.events.unsubscribe_event(name, callback)

    def emit(self, name, **kw):
        self.events.emit(name, **kw)

    ##########
    # Features


    def _subscribe_foreign_features(self):
        self.features.subscribe_foreign_features()

    def _unsubscribe_foreign_features(self):
        self.features.unsubscribe_foreign_features()

    # Public Feature API

    def list_features(self):
        return self.features.list_features()

    def has_foreign_feature(self, servicename, featurename):
        return self.features.has_foreign_feature(servicename, featurename)

    def subscribe_feature(self, feature, instance):
        return self.features.subscribe_feature(feature, instance)

    def unsubscribe_feature(self, feature_object):
        self.features.unsubscribe_feature(feature_object)

    def subscribe_foreign_feature(self, servicename, feature, instance):
        return self.boss.subscribe_feature(servicename, feature, instance)

    def unsubscribe_foreign_feature(self, servicename, feature_object):
        self.boss.unsubscribe_feature(servicename, feature_object)

    ##########
    # Actions

    def _unregister_actions_config(self):
        self.actions.remove_actions()

    def _subscribe_keyboard_shortcuts(self):
        self.actions.subscribe_keyboard_shortcuts()


    def get_action_group(self):
        return self.actions.get_action_group()

    def get_action(self, name):
        return self.actions.get_action(name)

    def get_keyboard_options(self):
        return self.actions.get_keyboard_options()

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


