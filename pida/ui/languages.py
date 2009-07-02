import gtk
from pida.utils.languages import Documentation


class PidaDocWindow(gtk.Window):
    """
    Window which is used to display documentation
    """
    def __init__(self, documentation=None, path=None, short=None, long_=None):
        super(PidaDocWindow, self).__init__(gtk.WINDOW_POPUP)
        #self.
        self.set_name('pida-docwindow')
        #self.set_name('gtk-tooltip')
#         self.container
        self.path = path
        self.short = short
        self.long_ = long_
        self.vars = []
        if isinstance(documentation, Documentation):
            documentation = [documentation]
        for doc in documentation:
            if not doc.short and not doc.long_ and not doc.path:
                continue
            self.vars.append({
                'short': doc.short,
                'long': doc.long_,
                'path': doc.path
            })
        self.valid = len(self.vars) > 0
        self.build_ui()

    def on_keypress(self, event):
        if event.type == gtk.gdk.KEY_PRESS and \
            event.keyval == gtk.keysyms.Escape:
                self.destroy()

    def build_ui(self):
        self.container = gtk.VBox()
        for var in self.vars:
            if var.get('path', None):
                sm = gtk.Label()
                sm.set_name('path')
                sm.set_justify(gtk.JUSTIFY_CENTER)
                sm.set_selectable(True)
                sm.set_markup("<b>%s</b>" %var.get('path'))
                sm.set_alignment(0, 0)
                self.container.pack_start(sm, expand=True, fill=True, padding=2)
                sm.show_all()
                self.pl = sm
            if var.get('short', None):
                sm = gtk.Label('bla\nblubb')
                sm.set_name('short')
                sm.set_justify(gtk.JUSTIFY_LEFT)
                sm.set_selectable(True)
                sm.set_markup("<b>%s</b>" %var.get('short'))
                sm.set_alignment(0, 0)
                self.container.pack_start(sm, expand=True, fill=True, padding=2)
                sm.show()
                self.sl = sm
            if var.get('long', None):
                sm = gtk.Label('test')
                sm.set_name('long')
                sm.set_justify(gtk.JUSTIFY_LEFT)
                sm.set_selectable(True)
                sm.set_markup("%s" %var.get('long'))
                sm.set_alignment(0, 0)
                self.container.pack_start(sm, expand=True, fill=True, padding=3)
                self.ll = sm
                sm.show()
        self.container.show()
        self.add(self.container)

    def present(self):
        super(PidaDocWindow, self).present()
        if hasattr(self, 'pl'):
            self.pl.select_region(0, 0)
        if hasattr(self, 'll'):
            self.ll.select_region(0, 0)
        if hasattr(self, 'sl'):
            self.sl.select_region(0, 0)

