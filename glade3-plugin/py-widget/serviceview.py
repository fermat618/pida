
import gobject
import gtk


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


def test():
    from gtk.glade import XML
    XML('test.glade').get_widget('window1').show_all()
    gtk.main()

if __name__ == '__main__':
    test()

