
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


from pida.core.options import OTypeBoolean, OTypeString, OTypeInteger, \
    OTypeStringList


class CleverProxyColorButton(ProxyColorButton):

    def update(self, val):
        col = gtk.gdk.color_parse(val)
        super(CleverProxyColorButton, self).update(col)

    def read(self):
        col = super(CleverProxyColorButton, self).read()
        return gdk_color_to_string(col)


def get_widget_for_type(rtype_instance):
    rtype = rtype_instance.__class__
    if rtype is OTypeBoolean:
        return ProxyCheckButton()
    elif rtype is OTypeStringList:
        return ProxyEntry()
    #elif rtype is types.file:
    #    w = ProxyFileChooserButton('Select File')
        #w.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    #    return w
    #elif rtype is types.readonlyfile:
    #    w = ProxyFileChooserButton('Select File')
    #    w.set_sensitive(False)
    #    #w.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    #    return w
    #elif rtype in [types.directory]:
    #    w = ProxyFileChooserButton(title='Select Directory')
    #    w.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    #    return w
    #elif rtype is types.font:
    #    return ProxyFontButton()
    #elif rtype is types.color:
    #    return CleverProxyColorButton()
    elif rtype is OTypeInteger:
        w = ProxySpinButton()
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
 
