
from protocols import Interface

from pida.core.plugins import Registry


class IBaseConfig(Interface):

    def create_all():
        """Create all the items in this configuration"""

    def bind_all():
        """Bind all the bindables in this configuration"""


class IOptionsConfig(IBaseConfig):

    def add_group(name, label, doc):
        """Add a configuration group"""

    def add_option(group, name, label, doc):
        """Add a configuration group"""


class IService(Interface):

    def get_name():
        """Get the name for the service"""

    def register_all_config():
        """Register all the configs"""
    
    def register_options_config(config):
        """Register the class for options config"""


class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create_all()

    def create_all(self):
        """Override to do the creations"""

    def bind_all(self):
        """Override to do the bindings"""

    def get_service_name(self):
        return self.svc.get_name()


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc):
        self.name = name
        self.label = label
        self.rtype = rtype
        self.doc = doc
        self.default = default
        self.value = default


class OptionsConfig(BaseConfig):

    def create_all(self):
        self._options = {}
        self.create_options()

    def create_options(self):
        """Create the options here"""

    def create_option(self, name, label, rtype, default, doc):
        opt = OptionItem(self, name, label, rtype, default, doc)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]
        

class Service(object):

    options_config = OptionsConfig

    def __init__(self, boss=None):
        self.boss = boss
        self.reg = Registry()
        self._register_all_config()

    def _register_all_config(self):
        self._register_options_config(self.options_config)

    def _register_options_config(self, config_cls):
        self.reg.register_plugin(
            instance=config_cls(self),
            singletons=(IOptionsConfig,)
        )

    def get_options(self):
        return self.reg.get_singleton(IOptionsConfig)

    def get_option(self, name):
        return self.get_options().get_option(name)

    def opt(self, name):
        return self.get_option(name).value



