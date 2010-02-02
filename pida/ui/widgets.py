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
from kiwi.utils import gsignal

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
        if isinstance(col, str):
            return col
        return gdk_color_to_string(col)


class ProxyStringList(gtk.VBox):

    gsignal('content-changed')

    def __init__(self):
        gtk.VBox.__init__(self, spacing=3)
        self.set_border_width(6)
        self.set_size_request(0, 150)
        #XXX: use plain Treeview ?!

        self.store = gtk.ListStore(str)
        self.view = gtk.TreeView()
        self.view.set_headers_visible(False)
        self.view.set_model(self.store)
        #XXX: scrollable?
        self.pack_start(self.view, expand=True)

        self.tv_col = gtk.TreeViewColumn()
        self.text_renderer = gtk.CellRendererText()
        self.tv_col.pack_start(self.text_renderer)
        self.tv_col.add_attribute(self.text_renderer, 'text', 0)

        self.view.append_column(self.tv_col)

        selection = self.view.get_selection()
        selection.connect('changed', self._on_selection_changed)

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
        iter = self.store.append(["New Item"])
        self.view.get_selection().select_iter(iter)
        self._emit_changed()

    def _on_rem(self, button):
        if self._current:
            self.store.remove(self._current)
            self._current = None
            self.view.get_selection().unselect_all()
        self._emit_changed()

    def _on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        self.rem_button.set_sensitive(iter is not None)
        self._current = iter
        if iter is not None:
            self.value_entry.set_sensitive(True)
            self.value_entry.set_text(model[iter][0])
        else:
            self.value_entry.set_sensitive(False)
            self.value_entry.set_text('')

    def _on_value_changed(self, entry):
        if self._current is  not None:
            self._block = True
            self.store.set(self._current, 0, entry.get_text())
            self._emit_changed()

    def _emit_changed(self) :
        self.emit('content-changed')
        
    def update(self, value):
        if not self._block: 
            self.store.clear()
            for item in value:
                self.store.append([item])
        self._block = False

    def read(self):
        return [i[0] for i in self.store]

    value = property(read, update)


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
    list: ProxyStringList,
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

