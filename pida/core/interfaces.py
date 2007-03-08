
from protocols import Interface


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


