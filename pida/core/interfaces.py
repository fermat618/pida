
from protocols import Interface


class IBaseConfig(Interface):

    def create():
        """Create all the items in this configuration"""


class IOptions(IBaseConfig):

    def add_option(group, name, label, doc):
        """Add a configuration group"""


class IEvents(IBaseConfig):

    def create_event(name):
        """Create an Event"""


class ICommands(IBaseConfig):
    
    """The commands for a plugin"""


class IFeatures(IBaseConfig):
    
    """The features for a plugin"""


class IService(Interface):

    def get_name():
        """Get the name for the service"""

