
import gtk, gobject

class PopupWindow(gtk.Window):

    __gtype_name__ = 'PopupWindow'

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_decorated(False)
        self.add_events(gtk.gdk.FOCUS_CHANGE_MASK)
        #self.connect('set-focus-child', self.on_focus_child)
        self.connect('focus-out-event', self.focus_out)

    def focus_out(self, window, event):
        print window, event

    #def do_set_focus_child(self, widget):
    #    print widget

gobject.type_register(PopupWindow)

class PopupEntryWindow(PopupWindow):

    def __init__(self):
        PopupWindow.__init__(self)
        hb = gtk.HBox()
        self.add(hb)
        vb = gtk.VBox()
        hb.pack_start(vb, expand=False)
        vb.set_border_width(6)
        self._title_label = gtk.Label()
        vb.pack_start(self._title_label, expand=False)
        self._primary_label = gtk.Label()
        vb.pack_start(self._primary_label, expand=False)
        self._secondary_label = gtk.Label()
        hb.pack_start(self._secondary_label, expand=False)
        self._entries = {}

    def add_entry(self, name, label):
        entry = gtk.Entry()
        entry.connect('changed', self.on_entry_changed, name)
        vb.pack_start(entry, expand=False)
        self._entries[name] = entry

    def grab_entry(self):
        self._entry.grab_focus()

    def set_title_label(self, value):
        self._title_label.set_text(value)

    def set_primary_label(self, value):
        self._primary_label.set_text(value)

    def set_secondary_label(self, value):
        self._secondary_label.set_text(value)

    def on_entry_changed(self, entry):
        self.set_secondary_label(entry.get_text())


if __name__ == '__main__':
    w1 = gtk.Window()
    w1.resize(400, 400)
    w1.add(gtk.TextView())
    w1.show_all()
    w = PopupEntryWindow()
    w.set_transient_for(w1)
    w.show_all()
    w.set_title_label('banana')
    gtk.main()

