import gtk, gobject

from kiwi.ui.delegates import GladeSlaveDelegate, SlaveDelegate
from kiwi.utils import gsignal, gproperty, type_register, PropertyObject



try:
    from pida.core.environment import get_pixmap_path
except ImportError:
    get_pixmap_path = lambda name: '/home/ali/working/pida-next/resources/pixmaps/%s' % name

from pida.utils.unique import create_unique_id

from pida.ui.docks import BEH_NORMAL

class PidaViewWidget(PropertyObject, gtk.VBox):

    __gtype_name__ = 'PidaViewWidget'

    gproperty('title-text', str, default='Untitled Pida View')

    gsignal('close-clicked')
    gsignal('detach-clicked')

    def __init__(self):
        gtk.VBox.__init__(self)
        self._child = None
        self._create_ui()
        PropertyObject.__init__(self)

    def _create_ui(self):
        self._create_top_bar()
        self._create_widget_holder()

    def _create_top_bar(self):
        self._top_bar = gtk.HBox()
        self.pack_start(self._top_bar, expand=False)
        self._title_label = gtk.Label()
        self._top_bar.pack_start(self._title_label)
        self._top_buttons = gtk.HBox()
        self._top_bar.pack_start(self._top_buttons, expand=False)
        self._detach_button = gtk.ToolButton(icon_widget=self._create_detach_button())
        self._top_buttons.pack_start(self._detach_button)
        self._close_button = gtk.ToolButton(icon_widget=self._create_close_button())
        self._top_buttons.pack_start(self._close_button)

    def _create_widget_holder(self):
        self._widget_holder = gtk.Frame()
        self.pack_start(self._widget_holder)

    def _create_close_button(self):
        im = gtk.Image()
        im.set_from_file(get_pixmap_path('view_close.gif'))
        return im

    def _create_detach_button(self):
        im = gtk.Image()
        im.set_from_file(get_pixmap_path('view_detach.gif'))
        return im

    def prop_set_title_text(self, val):
        if val is not None:
            self._title_label.set_text(val)

    def add_main_widget(self, child):
        self._widget_holder.add(child)
        self._child = child

    def remove_main_widget(self):
        self._widget_holder.remove(self._child)

    def get_main_widget(self):
        return self._child

    def do_add(self, widget):
        self.add_main_widget(widget)


class PidaViewMixin(object):

    icon_name = gtk.STOCK_INFO
    label_text = 'Pida View'
    dock_behaviour = BEH_NORMAL


    def create_ui(self):
        """Create the user interface here"""

    def get_unique_id(self):
        return self._uid

    def create_tab_label_icon(self):
        return gtk.image_new_from_stock(self.icon_name, gtk.ICON_SIZE_MENU)

    def get_tab_label_text(self):
        return self.label_text

class PidaGladeView(GladeSlaveDelegate, PidaViewMixin):

    def __init__(self, service, title=None, *args, **kw):
        self.svc = service
        GladeSlaveDelegate.__init__(self, *args, **kw)
        self._uid = create_unique_id()
        self.label_text = title or self.label_text
        self.create_ui()

class PidaView(SlaveDelegate, PidaViewMixin):

    def __init__(self, service, title=None, *args, **kw):
        self.svc = service
        self._main_widget = gtk.VBox()
        SlaveDelegate.__init__(self, toplevel=self._main_widget, *args, **kw)
        self._uid = create_unique_id()
        self.label_text = title or self.label_text
        self.create_ui()

    def add_main_widget(self, widget, *args, **kw):
        self._main_widget.pack_start(widget, *args, **kw)


