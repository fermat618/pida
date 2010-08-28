# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import pango

from pida.core.options import Color
from pygtkhelpers.ui.widgets import StringList
from pygtkhelpers import proxy


# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class CleverColorButtonProxy(proxy.GtkColorButtonProxy):

    def update(self, val):
        col = gtk.gdk.color_parse(val)
        super(CleverColorButtonProxy, self).update(col)

    def read(self):
        col = super(CleverColorButtonProxy, self).read()
        if isinstance(col, str):
            return col
        return col.to_string()


def _file_widget():
    w = gtk.FileChooserButton(_('Select File'))
    w.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    return w

def _integer_adjustment():
    w = gtk.SpinButton()
    w.set_adjustment(gtk.Adjustment(0, 0, 10000, 1))
    return w


type_to_proxy = {
    int: _integer_adjustment,
    bool: gtk.CheckButton,
    list: StringList,
    file: _file_widget,
    Color: gtk.ColorButton,
    pango.Font: gtk.FontButton,
    # readonly items?
    # choosing a directory?
    # choosing a readonly file? FILE_CHOOSER_ACTION_SAVE "Select File"
    # range
    }

def get_proxy_for_widget(widget):
    if isinstance(widget, gtk.ColorButton):
        return CleverColorButtonProxy(widget)
    return proxy.widget_proxies[widget.__class__](widget)


def get_widget_for_type(typ):
    if typ in type_to_proxy:
        return type_to_proxy[typ]()
    if issubclass(typ, str) and typ is not str:
        w = gtk.ComboBox()
        model = gtk.ListStore(str, str)
        w.set_model(model)

        if isinstance(typ.options, dict):
            items = [[l, v] for (v, l) in typ.options.iteritems()]
        else:
            items = [[v, v] for v in typ.options]
        for item in items:
            model.append(item)

        cell = gtk.CellRendererText()
        w.pack_start(cell, True)
        w.add_attribute(cell, 'text', 0)

        return w
        
    else:
        w = gtk.Entry()
        w.set_width_chars(18)
        return w
 #elif type.__name__ is 'intrange':
    #    adjvals = type.lower, type.upper, type.step
    #    adj = gtk.Adjustment(0, *adjvals)
    #    w = ProxySpinButton()
    #    w.set_adjustment(adj)
    #    return w
    #elif type is types.readonly:
    #    return FormattedLabel(VC_NAME_MU)
    #elif type.__name__ is OTypeStringList:
    #    return w

