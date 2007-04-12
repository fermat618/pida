import gtk
from moo.utils import BigPaned, PaneLabel

PANE_TERMINAL = 'Terminal'
PANE_EDITOR = 'Editor'
PANE_BUFFER = 'Buffer'
PANE_PLUGIN = 'Plugin'

POS_MAP = {
    PANE_TERMINAL: gtk.POS_BOTTOM,
    PANE_BUFFER: gtk.POS_LEFT,
    PANE_PLUGIN: gtk.POS_RIGHT,
}

class PidaPaned(BigPaned):

    def __init__(self):
        BigPaned.__init__(self)
        self.set_property('enable-detaching', True)

    def add_view(self, name, view):
        if name == PANE_EDITOR:
            self.add_child(view.get_toplevel())
        else:
            POS = POS_MAP[name]
            lab = PaneLabel(view.icon_name, None, None, view.label_text)
            self.insert_pane(view.get_toplevel(), lab, POS, POS)
            self.show_all()
            self.present_pane(view.get_toplevel())

from gtk import gdk

class Paned(gtk.Bin):

    """May the force be with me"""
    __gtype_name__ = 'MyPaned'

    def __init__(self):
        gtk.Bin.__init__(self)
        self._button_box = gtk.HButtonBox()
        self._button_box.set_parent(self)
        self._button_box.pack_start(gtk.Button(stock=gtk.STOCK_OK))
        self._button_box.show_all()

    def do_size_allocate(self, allocation):
        print 'sa'
        label_height = self._button_box.get_child_requisition () [1]
        #border_width = self.get_border_width ()
 
        self._button_box.size_allocate (gdk.Rectangle (allocation.x,
                                                       allocation.y,
                                                       allocation.width - 2,
                                                       label_height))
        self.allocation = allocation

    def do_size_request(self, req):
        print 'dsr'
        req.width, req.height = self._button_box.size_request()


    #def do_realize(self):
    #    self.set_flags(self.flags() | gtk.REALIZED)
        #self.window = gdk.Window(
		#    self.get_parent_window(),
		#    width=self.allocation.width - 20,
		#    height=self.allocation.height - 20,
        #    x = 20,
        #    y = 20,
		#    window_type=gdk.WINDOW_CHILD,
		#    wclass=gdk.INPUT_OUTPUT,
		#    event_mask=self.get_events() | gdk.EXPOSURE_MASK)

        #self.window.set_user_data(self)
        #self.style.attach(self.window)
        #self._button_box.realize()
        #self._button_box.window.reparent(self.window)

    def do_forall(self, internals, callback, data):
        print 'dofa'
        if internals:
            callback(self._button_box, data)


    #def do_unrealize(self):
    #    self.window.destroy()

    #def do_expose_event(self, event):
    #    print 'propogate expose'
    #    self.propagate_expose(self._button_box, event)

import gobject
gobject.type_register(Paned)
        
if __name__ == '__main__':
    p = Paned()
    w = gtk.Window()
    w.add(p)
    w.show_all()
    gtk.main()



