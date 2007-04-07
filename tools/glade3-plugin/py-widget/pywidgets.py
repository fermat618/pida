import gtk, gobject
import glade

class ServiceView(gtk.VBox):

    __gtype_name__ = 'ServiceView'

    def __init__(self):
        self._frame = gtk.Frame()
        self.pack_start(self._frame)
        self._bb = gtk.HButtonBox()
        self._bb.set_layout(gtk.BUTTONBOX_END)
        self._bb.pack_start(gtk.Button(stock=gtk.STOCK_CLOSE))
        self.pack_start(self._bb, expand=False)

    def add_main_widget(self, widget):
        self._frame.add(widget)

    def remove_main_widget(self, widget):
        self._frame.remove(widget)

    def do_add(self, widget):
        self.add_main_widget(widget)

class ServiceViewAdaptor(glade.get_adaptor_for_type('GtkVBox')):

    __gtype_name__ = 'ServiceViewAdaptor'

    def do_post_create(self, sv, reason):
        sv.add_main_widget(gobject.new('GladePlaceholder'))

    def do_get_children(self, obj):
        return obj._frame.get_children()

    def do_add(self, sv, child):
        sv.add_main_widget(child)

    def do_remove(self, sv, child):
        sv.remove_main_widget(child)

    def do_child_get_property(self, sv, child, prop):
        if prop in ['expand', 'fill']:
            return True
        elif prop == 'padding':
            return 0
        elif prop == 'position':
            return 0
        elif prop == 'pack-type':
            return gtk.PACK_START
        return True

    def do_child_set_property(self, sv, child, prop, val):
        if prop in ['expand', 'fill', 'padding', 'pack-type']:
            pass

    def do_replace_child(self, sv, old, new):
        sv.remove_main_widget(old)
        sv.add_main_widget(new)

    #def do_child_verify_property(self, sv, *args):
    #    print 'dcvp', args

    #def do_get_internal_child(self, sv, *args):
    #    print 'dgic', sv, args


