import gtk
from moo_stub import BigPaned, PaneLabel, PaneParams
from pida.utils.gthreads import gcall

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
        for pane in self.get_all_paneds():
            pane.set_pane_size(200)
            #pane.set_sticky_pane(True)

    def get_all_pos(self):
        return [gtk.POS_BOTTOM, gtk.POS_LEFT, gtk.POS_RIGHT]
        
    def get_all_paneds(self):
        for pos in self.get_all_pos():
            yield self.get_paned(pos)

    def add_view(self, name, view, present=False):
        if name == PANE_EDITOR:
            self.add_child(view.get_toplevel())
        else:
            POS = POS_MAP[name]
            lab = PaneLabel(view.icon_name, None, view.label_text)
            self.insert_pane(view.get_toplevel(), lab, POS, POS)
            if present:
                gcall(self.present_pane, view.get_toplevel())
            self.show_all()

    def remove_view(self, view):
        self.remove_pane(view.get_toplevel())

    def detach_view(self, view, size=(400,300)):
        paned, pos = self.find_pane(view.get_toplevel())
        paned.detach_pane(pos)
        self._center_on_parent(view, size)

    def present_view(self, view):
        paned, pos = self.find_pane(view.get_toplevel())
        paned.present_pane(pos)

    def _center_on_parent(self, view, size):
        gdkwindow = view.get_parent_window()
        px, py, pw, ph, pbd = view.svc.boss.get_window().window.get_geometry()
        w, h = size
        cx = (pw - w) / 2
        cy = (ph - h) / 2
        gdkwindow.move_resize(cx, cy, w, h)
        #gdkwindow.resize(w, h)

