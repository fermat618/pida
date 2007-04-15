import gtk
from moo_stub import BigPaned, PaneLabel
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
            pane.set_pane_size(150)
            pane.set_sticky_pane(True)

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
            lab = PaneLabel(view.icon_name, None, None, view.label_text)
            self.insert_pane(view.get_toplevel(), lab, POS, POS)
            def _present():
                self.present_pane(view.get_toplevel())
            if present:
                gcall(present)
            self.show_all()


