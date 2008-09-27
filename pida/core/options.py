import gconf

from pida.core.base import BaseConfig
from pida.core.environment import is_safe_mode, killsettings
from pango import Font


class OptionsManager(object):

    def __init__(self, session=None, boss=None):
        self._client = gconf.client_get_default()
        self.initialize_gconf()
        self._session = None
        if session:
            self.session = session
        if killsettings():
            self.unset_directory()

    def initialize_gconf(self):
        self.add_directory()
        self.add_directory('keyboard_shortcuts')
        self.add_directory('_sessions')

    def initialize_session(self):
        self.add_directory('_sessions', self.session)

    def _set_session(self, value):
        self._session = value
        self.initialize_session()
        
    def _get_session(self):
        if not self._session:
            # we need this form of lazy loading because the default manager
            # is created so early that the session name is not known then
            import pida.core.environment
            self.session = pida.core.environment.session_name()
        return self._session
        
    session = property(_get_session, _set_session)

    def add_directory(self, *parts):
        self._client.add_dir(
            '/'.join(['/apps/pida'] + list(parts)),
            gconf.CLIENT_PRELOAD_NONE
        )

    def add_service_directory(self, service):
        self.add_directory(service.get_name())

    def unset_directory(self, *parts):
        self._client.recursive_unset('/'.join(['/apps/pida'] + list(parts)), -1)

    def register_option(self, option):
        val = self._client.get(option.key)
        if val is None:
            self.set(option, option.default)
        if option.callback is not None:
            self.add_notify(option, option.callback)

    def add_notify(self, option, callback, *args):
        args = tuple([option] + list(args))
        if len(args) == 1:
            args = args[0]
        self._client.notify_add(option.key, callback, args)

    def get(self, option):
        key, type = option.key, option.type
        c = self._client
        if type in (str, file, Font):
            return c.get_string(key)
        elif issubclass(type, str):
            return c.get_string(key)
        elif type is bool:
            return c.get_bool(key)
        elif type in (int, long):
            return c.get_int(key)
        elif type is list:
            return c.get_list(key, gconf.VALUE_STRING)
        else:
            raise TypeError('unknown option type',type)


    def set(self, option, value):
        key, rtype = option.key, option.type
        c = self._client
        if rtype in (str, file, Font):
            c.set_string(key, value)
        elif issubclass(rtype, str):
            c.set_string(key, value)
        elif rtype is bool:
            c.set_bool(key, value)
        elif rtype in (int, long):
            c.set_int(key, value)
        elif rtype is list:
            c.set_list(key, gconf.VALUE_STRING, value)
        else:
            raise TypeError('unknown option type',rtype)

def choices(choices):
    """Helper to generate string options for choices"""
    class Choices(str):
        """
        Option that should be one of the choices
        """
        options = choices
    return Choices

class Color(str):
    """
    Option which is a color in RGB Hex
    """
    pass


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc, callback, 
                 session=None):
        self.group = group
        self.name = name
        self.label = label
        self.type = rtype
        self.doc = doc
        self.default = default
        if session:
            self.key = '/apps/pida/_sessions/%s/%s/%s' % (
                            manager.session, self.group, self.name)
        else:
            self.key = '/apps/pida/%s/%s' % (self.group, self.name)
        self.callback = callback

    def get_value(self):
        return manager.get(self)

    def set_value(self, value):
        return manager.set(self, value)

    value = property(get_value, set_value)

    def add_notify(self, callback, *args):
        manager.add_notify(self, callback, *args)

manager = OptionsManager()

class OptionsConfig(BaseConfig):

    def create(self):
        self._options = {}
        self.create_options()
        self.register_options()

    def create_options(self):
        """Create the options here"""

    def register_options(self):
        manager.add_service_directory(self.svc)
        for option in self._options.values():
            manager.register_option(option)

    def create_option(self, name, label, type, default, doc, callback=None, 
                      safe=True, session=False):
        opt = OptionItem(self.svc.get_name(), name, label, type, default, doc,
                         callback, session)
        self.add_option(opt)
        # in safemode we reset all dangerouse variables so pida can start
        # even if there are some settings + pida bugs that cause problems
        # default values MUST be safe
        if not safe and is_safe_mode():
            self.set_value(name, default)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]

    def get_value(self, optname):
        return manager.get(self.get_option(optname))

    def set_value(self, optname, value):
        return manager.set(self.get_option(optname), value)

    def __len__(self):
        return len(self._options)

    def __iter__(self):
        return self._options.itervalues()

    def __nonzero__(self):
        return bool(self._options)

