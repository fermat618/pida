# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from cgi import escape

import gtk
import gobject
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
from kiwi.utils import gsignal

from kiwi.ui.objectlist import ObjectList, Column

from pida.core.options import Color

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
        return gdk_color_to_string(col)


class ProxyStringListItem(object):

    def __init__(self, value):
        self.value = value

class ProxyStringList(gtk.VBox):

    gsignal('content-changed')

    def __init__(self):
        gtk.VBox.__init__(self, spacing=3)
        self.set_border_width(6)
        self.set_size_request(0, 150)
        self._ol = ObjectList([Column('value', expand=True)])
        self._ol.set_headers_visible(False)
        self._ol.connect('selection_changed', self._on_ol_selection)
        self._ol.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(self._ol)
        hb = gtk.HButtonBox()
        self.value_entry = gtk.Entry()
        self.value_entry.connect('changed', self._on_value_changed)
        self.value_entry.set_sensitive(False)
        self.pack_start(self.value_entry, expand=False)
        self.add_button = gtk.Button(stock=gtk.STOCK_NEW)
        self.add_button.connect('clicked', self._on_add)
        hb.pack_start(self.add_button, expand=False)
        self.rem_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.rem_button.connect('clicked', self._on_rem)
        self.rem_button.set_sensitive(False)
        hb.pack_start(self.rem_button, expand=False)
        self.pack_start(hb, expand=False)
        self._current =  None
        self._block = False
        
    def _on_add(self, button):
        item = ProxyStringListItem('New Item')
        self._ol.append(item, select=True)
        self._emit_changed()

    def _on_rem(self, button):
        self._ol.remove(self._current, select=True)
        self._emit_changed()

    def _on_ol_selection(self, ol, item):
        self.rem_button.set_sensitive(item is not None)
        self._current = item
        if item is not None:
            self.value_entry.set_text(item.value)
            self.value_entry.set_sensitive(True)
        else:
            self.value_entry.set_sensitive(False)
            self.value_entry.set_text('')

    def _on_value_changed(self, entry):
        if self._current is not None:
            self._block = True
            self._current.value = entry.get_text()
            self._ol.update(self._current)
            self._emit_changed()

    def _emit_changed(self):
        self.emit('content-changed')
        
    def update(self, value):
        if not self._block:
            self._ol.add_list(self.create_items(value))
        self._block = False

    def read(self):
        return [i.value for i in self._ol]

    def create_items(self, value):
        return [ProxyStringListItem(v) for v in value]


def get_widget_for_type(typ):
    if typ is bool:
        return ProxyCheckButton()
    elif typ is list:
        return ProxyStringList()
    elif typ is file:
        w = ProxyFileChooserButton(_('Select File'))
        w.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        return w
    #elif type is types.readonlyfile:
    #    w = ProxyFileChooserButton('Select File')
    #    w.set_sensitive(False)
    #    #w.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    #    return w
    #elif type in [types.directory]:
    #    w = ProxyFileChooserButton(title='Select Directory')
    #    w.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    #    return w
    elif typ is Color:
        return CleverProxyColorButton()
    elif typ is pango.Font:
        return ProxyFontButton()
    #elif type is types.color:
    #    
    elif typ is int:
        w = ProxySpinButton()
        w.set_adjustment(gtk.Adjustment(0, 0, 10000, 1))
        return w
    elif issubclass(typ, str) and typ is not str:
        w = ProxyComboBox()
        if type(typ.options) is dict:
            w.prefill([(l, v) for (v, l) in typ.options.iteritems()])
        else:
            w.prefill([(v, v) for v in typ.options])
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
    else:
        w = ProxyEntry(data_type=str)
        w.set_width_chars(18)
        return w
 
