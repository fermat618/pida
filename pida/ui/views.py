# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

from pygtkhelpers.delegates import SlaveView

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext



class PidaView(SlaveView):

    # Set this to make your views memorable.
    key = None

    icon_name = gtk.STOCK_INFO
    label_text = _('Pida View')

    pane = None

    def create_ui(self):
        """Create the user interface here"""

    def create_tab_label_icon(self):
        return gtk.image_new_from_stock(self.icon_name, gtk.ICON_SIZE_MENU)

    def get_parent_window(self):
        return self.toplevel.get_parent_window()

    parent_window = property(get_parent_window)

    def on_remove_attempt(self, pane):
        return not self.can_be_closed()

    def can_be_closed(self):
        return False

    gladefile = None

    def __init__(self, service, title=None, icon=None, *args, **kw):
        if not self.builder_file:
            self.builder_file = self.gladefile
        self.svc = service
        self.label_text = title or self.label_text
        self.icon_name = icon or self.icon_name
        if self.key:
            pass
            #self.toplevel.set_name(self.key.replace(".", "_"))
        super(PidaView, self).__init__()

    def get_toplevel(self):
        return self.widget

    toplevel = property(get_toplevel)

    def add_main_widget(self, widget, *args, **kw):
        self.widget.pack_start(widget, *args, **kw)


PidaGladeView = PidaView


class WindowConfig(object):
    """
    WindowConfig objects are used to register
    a window in the windows service so they
    can get proper shortcuts
    """
    key = None
    label_text = ""
    description = ""
    default_shortcut = ""
    action = None
