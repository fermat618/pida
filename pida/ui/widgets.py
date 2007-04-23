
from cgi import escape

import gtk
import gobject
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

from pida.core.options import OTypeBoolean, OTypeString, OTypeInteger, \
    OTypeStringList, OTypeFile, OTypeFont, OTypeStringOption


class CleverProxyColorButton(ProxyColorButton):

    def update(self, val):
        col = gtk.gdk.color_parse(val)
        super(CleverProxyColorButton, self).update(col)

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
        self.set_size_request(0, 200)
        self._ol = ObjectList([Column('value', expand=True)])
        self._ol.set_headers_visible(False)
        self._ol.connect('selection_changed', self._on_ol_selection)
        self.pack_start(self._ol)
        hb = gtk.HButtonBox()
        self.value_entry = ProxyEntry()
        self.value_entry.connect('content-changed', self._on_value_changed)
        self.pack_start(self.value_entry, expand=False)
        self.add_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_button.connect('clicked', self._on_add)
        hb.pack_start(self.add_button, expand=False)
        self.rem_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.rem_button.connect('clicked', self._on_rem)
        hb.pack_start(self.rem_button, expand=False)
        self.pack_start(hb, expand=False)
        self._current =  None
        
    def _on_add(self, button):
        self._ol.append(ProxyStringListItem('no value'))
        self._emit_changed()

    def _on_rem(self, button):
        self._ol.remove(self._current)
        self._emit_changed()

    def _on_ol_selection(self, ol, item):
        self.value_entry.set_sensitive(item is not None)
        self.rem_button.set_sensitive(item is not None)
        self._current = item
        if item is None:
            self.value_entry.set_text('')
        else:
            self.value_entry.set_text(item.value)

    def _on_value_changed(self, entry):
        if self._current is not None:
            self._current.value = entry.read()
            self._ol.update(self._current)
            self._emit_changed()

    def _emit_changed(self):
        self.emit('content-changed')
        
    def update(self, value):
        self._ol.add_list(self.create_items(value))

    def read(self):
        return [i.value for i in self._ol]

    def create_items(self, value):
        return [ProxyStringListItem(v) for v in value]


def get_widget_for_type(rtype_instance):
    rtype = rtype_instance.__class__
    if rtype is OTypeBoolean:
        return ProxyCheckButton()
    elif rtype is OTypeStringList:
        return ProxyStringList()
    elif rtype is OTypeFile:
        w = ProxyFileChooserButton('Select File')
        w.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        return w
    #elif rtype is types.readonlyfile:
    #    w = ProxyFileChooserButton('Select File')
    #    w.set_sensitive(False)
    #    #w.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    #    return w
    #elif rtype in [types.directory]:
    #    w = ProxyFileChooserButton(title='Select Directory')
    #    w.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    #    return w
    elif rtype is OTypeFont:
        return ProxyFontButton()
    #elif rtype is types.color:
    #    return CleverProxyColorButton()
    elif rtype is OTypeInteger:
        w = ProxySpinButton()
        w.set_adjustment(gtk.Adjustment(0, 0, 10000, 1))
        return w
    elif isinstance(rtype_instance, OTypeStringOption):
        w = ProxyComboBox()
        w.prefill([(v, v) for v in rtype.options])
        return w
        
    #elif rtype.__name__ is 'intrange':
    #    adjvals = rtype.lower, rtype.upper, rtype.step
    #    adj = gtk.Adjustment(0, *adjvals)
    #    w = ProxySpinButton()
    #    w.set_adjustment(adj)
    #    return w
    #elif rtype is types.readonly:
    #    return FormattedLabel(VC_NAME_MU)
    #elif rtype.__name__ is OTypeStringList:
    #    return w
    else:
        w = ProxyEntry(data_type=str)
        w.set_width_chars(18)
        return w
 
