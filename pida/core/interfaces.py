#XXX: deprecated ?
try:
    from protocols import Interface
except ImportError:
    class Interface:
        """A dummy"""


class IBaseConfig(Interface):

    def create():
        """Create all the items in this configuration"""


class IOptions(IBaseConfig):

    def add_option(group, name, label, doc):
        """Add a configuration group"""


class IEvents(IBaseConfig):
    pass


class ICommands(IBaseConfig):
    
    """The commands for a plugin"""


class IFeatures(IBaseConfig):
    
    """The features for a plugin"""

class IActions(IBaseConfig):

    """The actions for a service"""

    def create_actions():
        """Create actions here"""

class IService(Interface):

    def get_name():
        """Get the name for the service"""

class IPlugin(Interface):
    """A plugin"""


class IEditor(Interface):

    def start():
        """Start the editor"""

    def started():
        """Called when the editor has started"""

    def get_current():
        """Get the current document"""

    def open(document):
        """Open a document"""

    def open_many(documents):
        """Open a few documents"""

    def close():
        """Close the current document"""

    def close_all():
        """Close all the documents"""

    def save():
        """Save the current document"""

    def save_as(filename):
        """Save the current document as another filename"""

    def revert():
        """Revert to the loaded version of the file"""

    def goto_line(linenumber):
        """Goto a line"""

    def cut():
        """Cut to the clipboard"""

    def copy():
        """Copy to the clipboard"""

    def paste():
        """Paste from the clipboard"""

    def grab_focus():
        """Grab the focus"""

    def set_undo_sensitive(sensitive):
        """Set the undo action sensitivity"""

    def set_redo_sensitive(sensitive):
        """Set the redo action sensitivity"""

    def set_save_sensitive(sensitive):
        """Set the save action sensitivity"""

    def set_revert_sensitive(sensitive):
        """Set the revert sensitivity"""


class IProjectController(Interface):

    """A Project Controller"""

class IFileManager(Interface):

    """A File Manager"""
