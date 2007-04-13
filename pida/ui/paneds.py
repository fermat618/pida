import gtk
from moo_stub import BigPaned, PaneLabel

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


