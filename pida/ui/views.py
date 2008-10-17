# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk, gobject

from kiwi.ui.delegates import GladeSlaveDelegate, SlaveDelegate
from kiwi.utils import gsignal, gproperty, type_register, PropertyObject



from pida.core.environment import get_pixmap_path

from pida.utils.unique import create_unique_id
from pida.ui.paneds import PaneLabel

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class PidaViewWidget(PropertyObject, gtk.VBox):

    __gtype_name__ = 'PidaViewWidget'

    gproperty('title-text', str, default=_('Untitled Pida View'))

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

    # Set this to make your views memorable.
    key = None

    icon_name = gtk.STOCK_INFO
    label_text = _('Pida View')

    pane = None

    def create_ui(self):
        """Create the user interface here"""

    def create_tab_label_icon(self):
        return gtk.image_new_from_stock(self.icon_name, gtk.ICON_SIZE_MENU)

    def get_tab_label_text(self):
        return self.label_text

    def get_parent_window(self):
        return self.get_toplevel().get_parent_window()

    parent_window = property(get_parent_window)

    def on_remove_attempt(self, pane):
        return not self.can_be_closed()

    def can_be_closed(self):
        return False

    def set_pane_label(self, label_text=None, icon_name=None):
        if self.pane is not None:
            if icon_name is None:
                icon_name = self.icon_name
            if label_text is None:
                label_text = self.label_text
            label = PaneLabel(icon_name, None, label_text)
            self.pane.set_property('label', label)
        else:
            self.svc.log.error(_('Attempted to set a pane label on a view '
                                 'which is not in a pane'))


class PidaGladeView(GladeSlaveDelegate, PidaViewMixin):

    def __init__(self, service, title=None, icon=None, *args, **kw):
        if hasattr(self, 'locale') and self.locale is not None:
            self.locale.bindglade()
        self.svc = service
        GladeSlaveDelegate.__init__(self, *args, **kw)
        self.label_text = title or self.label_text
        self.icon_name = icon or self.icon_name
        self.create_ui()
        if self.key:
            self.toplevel.set_name(self.key.replace(".", "_"))

class PidaView(SlaveDelegate, PidaViewMixin):

    def __init__(self, service, title=None, icon=None, *args, **kw):
        self.svc = service
        self._main_widget = gtk.VBox()
        SlaveDelegate.__init__(self, toplevel=self._main_widget, *args, **kw)
        self.label_text = title or self.label_text
        self.icon_name = icon or self.icon_name
        self.create_ui()
        if self.key:
            self.toplevel.set_name(self.key.replace(".", "_"))

    def add_main_widget(self, widget, *args, **kw):
        self._main_widget.pack_start(widget, *args, **kw)



