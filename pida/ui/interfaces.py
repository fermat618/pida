
from protocols import Interface

class IView(Interface):

    def get_unique_id(self):
        """Return the unique id for the view"""

    def get_toplevel(self):
        """Return the toplevel widget for the view"""

    def create_tab_label(self):
        """Create a tab label for the view"""
