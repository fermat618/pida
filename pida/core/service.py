"""
    pida.core.service
    ~~~~~~~~~~~~~~~~~

    Base classes for services/plugins.

    :copyright:
        * 2007-2008 Ali Afshar
        * 2007-2008 Ronny Pfannschmidt

    :license: GPL2 or later
"""

# PIDA Imports
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
        self.events.subscribe_all_foreign()
        self.features.subscribe_all_foreign()
        self.actions.subscribe_keyboard_shortcuts()

    def __repr__(self):
        #XXX: bad factoring, get better types
        if self.__class__.__module__.startswith('pida.service'):
            return '<Service: %s>'%self.__class__.__name__
        else:
            return '<Plugin: %s>'%self.__class__.__name__

    @classmethod
    def get_name(cls):
        return cls.__module__.split('.')[-1]

    @staticmethod
    def sort_key(service):
        """helper for sorting, use as key argument for `list.sort`/`sorted`"""
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
        self.events.unsubscribe_foreign()
        self.features.unsubscribe_foreign()
        self.actions.remove_actions()

    ##########
    # Options API
    def get_option(self, name):
        return self.options.get_option(name)

    def opt(self, name):
        return self.options.get_value(name)

    def set_opt(self, name, value):
        return self.options.set_value(name, value)

    def cmd(self, commandname, **kw):
        """delegates a command to the commandsconfig"""
        return self.commands(commandname, **kw)

    def emit(self, name, **kw):
        """delegates a emited event to the eventsconfig"""
        self.events.emit(name, **kw)

    ##########
    # Actions

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


