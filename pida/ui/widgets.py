# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import pango

from kiwi.ui.gadgets import gdk_color_to_string
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.fontbutton import ProxyFontButton
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.colorbutton import ProxyColorButton
from kiwi.ui.widgets.filechooser import ProxyFileChooserButton

from pida.core.options import Color
from pygtkhelpers.ui.widgets import StringList
# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class CleverProxyColorButton(ProxyColorButton):

    def update(self, val):
        col = gtk.gdk.color_parse(val)
        # kiwi api seems incompatible so we have to try :(
        try:
            super(CleverProxyColorButton, self).update(col)
        except TypeError:
            super(CleverProxyColorButton, self).update(col.to_string())

    def read(self):
        col = super(CleverProxyColorButton, self).read()
        if isinstance(col, str):
            return col
        return gdk_color_to_string(col)


def _file_widget():
    w = ProxyFileChooserButton(_('Select File'))
    w.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    return w

def _integer_adjustment():
    w = ProxySpinButton()
    w.set_adjustment(gtk.Adjustment(0, 0, 10000, 1))
    return w


type_to_proxy = {
    int: _integer_adjustment,
    bool: ProxyCheckButton,
    list: StringList,
    file: _file_widget,
    Color: CleverProxyColorButton,
    pango.Font: ProxyFontButton,
    # readonly items?
    # choosing a directory?
    # choosing a readonly file? FILE_CHOOSER_ACTION_SAVE "Select File"
    # range
    }

def get_widget_for_type(typ):
    if typ in type_to_proxy:
        return type_to_proxy[typ]()
    if issubclass(typ, str) and typ is not str:
        w = ProxyComboBox()
        if isinstance(typ.options, dict):
            w.prefill([(l, v) for (v, l) in typ.options.iteritems()])
        else:
            w.prefill([(v, v) for v in typ.options])
        return w
        
    else:
        w = ProxyEntry(data_type=str)
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

