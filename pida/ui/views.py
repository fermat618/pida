import gtk

from kiwi.ui.delegates import GladeSlaveDelegate

from pida.utils.unique import create_unique_id

class PidaView(GladeSlaveDelegate):

    icon_name = gtk.STOCK_INFO
    label_text = 'Pida View'

    def __init__(self, service, *args, **kw):
        self.svc = service
        GladeSlaveDelegate.__init__(self, *args, **kw)
        self._uid = create_unique_id()
        self.create_ui()

    def create_ui(self):
        """Create the user interface here"""

    def get_unique_id(self):
        return self._uid

    def create_tab_label_icon(self):
        return gtk.image_new_from_stock(self.icon_name, gtk.ICON_SIZE_MENU)

    def get_tab_label_text(self):
        return self.label_text

