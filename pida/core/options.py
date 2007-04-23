import gconf

from pida.core.base import BaseConfig

class OptionsManager(object):

    def __init__(self, boss=None):
        self._client = gconf.client_get_default()
        self.initialize_gconf()

    def initialize_gconf(self):
        self.add_directory('pida')
        self.add_directory('pida', 'keyboard_shortcuts')

    def add_directory(self, *parts):
        self._client.add_dir(
            '/'.join(['/apps'] + list(parts)),
            gconf.CLIENT_PRELOAD_NONE
        )

    def add_service_directory(self, service):
        self.add_directory('pida', service.get_name())
        
    def register_option(self, option):
        val = self._client.get(option.key)
        if val is None:
            option.set(self._client, option.default)
        if option.callback is not None:
            self._client.notify_add(option.key, option.callback, option)

    def get_value(self, option):
        return option.get(self._client)

    def set_value(self, option, value):
        return option.set(self._client, value)


class OTypeBase(object):

    @classmethod
    def _getter(cls, client):
        return getattr(client, 'get_%s' % cls.gconf_name)
    
    @classmethod
    def _setter(cls, client):
        return getattr(client, 'set_%s' % cls.gconf_name)

    @classmethod
    def get(cls, client, key):
        return cls._getter(client)(key)
        
    @classmethod
    def set(cls, client, key, value):
        return cls._setter(client)(key, value)
        
    

class OTypeString(OTypeBase):
    """A string configuration type"""

    gconf_name = 'string'


class OTypeBoolean(OTypeBase):
    """A Boolean configuration type"""

    gconf_name = 'bool'


class OTypeInteger(OTypeBase):
    """An integer configuration type"""

    gconf_name = 'int'


class OTypeStringList(OTypeBase):
    """A list of strings configuration type"""

    gconf_name = 'list'

    @classmethod
    def get(cls, client, key):
        return cls._getter(client)(key, gconf.VALUE_STRING)
        
    @classmethod
    def set(cls, client, key, value):
        return cls._setter(client)(key, gconf.VALUE_STRING, value)
    

class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc, callback):
        self.group = group
        self.name = name
        self.label = label
        self.rtype = rtype
        self.doc = doc
        self.default = default
        self.key = self._create_key()
        self.callback = callback

    def _create_key(self):
        return '/apps/pida/%s/%s' % (self.group, self.name)

    def get(self, client):
        return self.rtype.get(client, self.key)
        
    def set(self, client, value):
        return self.rtype.set(client, self.key, value)

    def get_value(self):
        return manager.get_value(self)

    def set_value(self, value):
        return manager.set_value(self, value)

    value = property(get_value, set_value)


manager = OptionsManager()

class OptionsConfig(BaseConfig):

    manager = manager

    def create(self):
        self._options = {}
        self.create_options()
        self.register_options()

    def create_options(self):
        """Create the options here"""

    def register_options(self):
        self.manager.add_service_directory(self.svc)
        for option in self._options.values():
            self.manager.register_option(option)

    def create_option(self, name, label, rtype, default, doc, callback=None):
        opt = OptionItem(self.svc.get_name(), name, label, rtype, default, doc,
                         callback)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]

    def get_value(self, optname):
        return self.manager.get_value(self.get_option(optname))

    def set_value(self, optname, value):
        return self.manager.set_value(self.get_option(optname), value)


