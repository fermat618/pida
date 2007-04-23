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
            self.add_notify(option, option.callback)

    def add_notify(self, option, callback, *args):
        args = tuple([option] + list(args))
        if len(args) == 1:
            args = args[0]
        self._client.notify_add(option.key, callback, args)

    def get_value(self, option):
        return option.get(self._client)

    def set_value(self, option, value):
        return option.set(self._client, value)


class OTypeBase(object):

    def _getter(self, client):
        return getattr(client, 'get_%s' % self.gconf_name)
    
    def _setter(self, client):
        return getattr(client, 'set_%s' % self.gconf_name)

    def get(self, client, key):
        return self._getter(client)(key)
        
    def set(self, client, key, value):
        return self._setter(client)(key, value)
        
    

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

    def get(self, client, key):
        return self._getter(client)(key, gconf.VALUE_STRING)
        
    def set(self, client, key, value):
        return self._setter(client)(key, gconf.VALUE_STRING, value)

class OTypeFile(OTypeString):

    """For files"""

class OTypeFont(OTypeString):
    
    """Fonts"""

class OTypeStringOption(OTypeString):
    
    """String from a list of options"""

# Awful
def otype_string_options_factory(options):
    return type('', (OTypeStringOption,), {'options': options})


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc, callback):
        self.group = group
        self.name = name
        self.label = label
        self.rtype = rtype()
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

    def add_notify(self, callback, *args):
        manager.add_notify(self, callback, *args)


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

    def __len__(self):
        return len(self._options)

    def iter_options(self):
        return self._options.values()


