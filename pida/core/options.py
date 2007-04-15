import gconf

from pida.core.base import BaseConfig

class OptionsManager(object):

    def __init__(self, boss=None):
        self._client = gconf.client_get_default()
        self.initialize_gconf()

    def initialize_gconf(self):
        self.add_directory('pida')

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

    def get_value(self, option):
        return option.get(self._client)


class OTypeString(object):
    """A string configuration type"""

    gconf_name = 'string'

class OTypeBoolean(object):
    """A Boolean configuration type"""

    gconf_name = 'bool'

class OTypeInteger(object):
    """An integer configuration type"""

    gconf_name = 'int'
    

class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc):
        self.group = group
        self.name = name
        self.label = label
        self.rtype = rtype
        self.doc = doc
        self.default = default
        self.value = default
        self.key = self._create_key()

    def _create_key(self):
        return '/apps/pida/%s/%s' % (self.group, self.name)

    def get(self, client):
        return self._getter(client)(self.key)
        
    def set(self, client, value):
        return self._setter(client)(self.key, value)

    #TODO move this to the option type
    def _getter(self, client):
        return getattr(client, 'get_%s' % self.rtype.gconf_name)

    def _setter(self, client):
        return getattr(client, 'set_%s' % self.rtype.gconf_name)


class OptionsConfig(BaseConfig):

    manager = OptionsManager()

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

    def create_option(self, name, label, rtype, default, doc):
        opt = OptionItem(self.svc.get_name(), name, label, rtype, default, doc)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]

    def get_value(self, optname):
        return self.manager.get_value(self.get_option(optname))

