
import glade
import gtk, gobject

import sys
sys.path.insert(0, '/home/ali/working/pida-next/')

from pida.core import environment


from pida.ui.views import PidaViewWidget
from vte import Terminal as VteTerminal

from kiwi.utils import gproperty, PropertyObject


class PidaViewWidgetAdaptor(glade.get_adaptor_for_type('GtkVBox')):

    __gtype_name__ = 'PidaViewWidgetAdaptor'

    def do_post_create(self, pvw, reason):
        pvw.add_main_widget(gobject.new('GladePlaceholder'))

    def do_replace_child(self, pvw, old, new):
        pvw.remove_main_widget()
        pvw.add_main_widget(new)

    def do_get_children(self, pvw):
        return [pvw.get_main_widget()]

    def do_add(self, pvw, child):
        pvw.add_main_widget(child)

    def do_remove(self, pvw, child):
        pvw.remove_main_widget()

    def do_child_get_property(self, pvw, child, prop):
        if prop in ['expand', 'fill']:
            return True
        elif prop == 'padding':
            return 0
        elif prop == 'position':
            return 0
        elif prop == 'pack-type':
            return gtk.PACK_START
        return True

    def do_child_set_property(self, pvw, child, prop, val):
        if prop in ['expand', 'fill', 'padding', 'pack-type']:
            pass





