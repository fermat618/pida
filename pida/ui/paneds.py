import os

import gtk

from pida.core.environment import pida_home

# Don't import moo twice from different locations when the full editor is
# being used.
try:
    import moo
    from moo.utils import BigPaned, PaneLabel, PaneParams
    from moo.utils import PANE_POS_BOTTOM, PANE_POS_TOP, PANE_POS_RIGHT, PANE_POS_LEFT
    version = moo.version.split('.')
    if ((int(version[0]) > 0) or
        ((int(version[1]) > 8) and (int(version[2]) > 0)) or
        (int(version[1]) > 9)):
        use_old = False
    else:
        use_old = True

except ImportError:
    from moo_stub import BigPaned, PaneLabel, PaneParams
    from moo_stub import PANE_POS_BOTTOM, PANE_POS_TOP, PANE_POS_RIGHT, PANE_POS_LEFT
    use_old = False



from pida.utils.gthreads import gcall

PANE_TERMINAL = 'Terminal'
PANE_EDITOR = 'Editor'
PANE_BUFFER = 'Buffer'
PANE_PLUGIN = 'Plugin'

POS_MAP = {
    PANE_TERMINAL: PANE_POS_BOTTOM,
    PANE_BUFFER: PANE_POS_LEFT,
    PANE_PLUGIN: PANE_POS_RIGHT,
}

class PidaPaned(BigPaned):

    def __init__(self):
        BigPaned.__init__(self)
        self._fullscreen = False
        self._fullscreen_vis = {}
        self.set_property('enable-detaching', True)
        self.connect('config-changed', self.on_config_changed)
        self.config_file = os.path.join(pida_home, 'paneconfig.txt')
        self.set_name('PidaBigPaned')
        self.init_config()

    def get_all_pos(self):
        return [PANE_POS_TOP, PANE_POS_LEFT, PANE_POS_RIGHT]

    def get_all_paneds(self):
        for pos in self.get_all_pos():
            yield self.get_paned(pos)

    def add_view(self, name, view, removable=True, present=True):
        if name == PANE_EDITOR:
            self.add_child(view.get_toplevel())
        else:
            POS = POS_MAP[name]
            lab = PaneLabel(view.icon_name, None, view.label_text)
            if use_old:
                pane = self.insert_pane(view.get_toplevel(), lab, POS, POS)
            else:
                pane = self.insert_pane(view.get_toplevel(), view.key, lab, POS, POS)
            view.pane = pane
            if not removable:
                pane.set_property('removable', False)
            pane.connect('remove', view.on_remove_attempt)
            view.toplevel.parent.set_name('PidaWindow')
            if present:
                gcall(self.present_pane, view.get_toplevel())
            self.show_all()

    def remove_view(self, view):
        self.remove_pane(view.get_toplevel())
        view.pane = None

    def detach_view(self, view, size=(400,300)):
        paned, pos = self.find_pane(view.get_toplevel())
        paned.detach_pane(pos)
        self._center_on_parent(view, size)

    def present_view(self, view):
        pane, pos = self.find_pane(view.get_toplevel())
        pane.present()

    def get_open_pane(self, name):
        POS = POS_MAP[name]
        paned = self.get_paned(POS)
        pane = paned.get_open_pane()
        return paned, pane

    def switch_next_pane(self, name):
        paned, pane = self.get_open_pane(name)
        if pane is None:
            num = -1
        else:
            num = pane.get_index()
        newnum = num + 1
        if newnum == paned.n_panes():
            newnum = 0
        newpane = paned.get_nth_pane(newnum)
        if newpane is None:
            # no pane exists
            return
        newpane.present()

    def switch_prev_pane(self, name):
        paned, pane = self.get_open_pane(name)
        if pane is None:
            num = paned.n_panes()
        else:
            num = pane.get_index()
        newnum = num - 1
        if newnum == -1:
            newnum = paned.n_panes() - 1
        if newnum < 0:
            # no pane exists
            return
        newpane = paned.get_nth_pane(newnum)
        newpane.present()

    def present_paned(self, name):
        paned, pane = self.get_open_pane(name)
        if pane is None:
            num = 0
        else:
            num = pane.get_index()
        pane = paned.get_nth_pane(num)
        if pane is not None:
            pane.present()

    def _center_on_parent(self, view, size):
        gdkwindow = view.get_parent_window()
        px, py, pw, ph, pbd = view.svc.window.window.get_geometry()
        w, h = size
        cx = (pw - w) / 2
        cy = (ph - h) / 2
        gdkwindow.move_resize(cx, cy, w, h)
        #gdkwindow.resize(w, h)

    def on_config_changed(self, bigpaned):
        self.write_config()

    def write_config(self):
        try:
            f = open(self.config_file, 'w')
            f.write(self.get_config())
            f.close()
        except IOError, OSError:
            pass

    def read_config(self):
        try:
            f = open(self.config_file, 'r')
            config = f.read()
            f.close()
            return config
        except IOError, OSError:
            return None

    def init_config(self):
        config = self.read_config()
        if config:
            self.set_config(config)

    def set_fullscreen(self, fullscreen):
        if self._fullscreen == fullscreen:
            return
        if fullscreen:
            for pos in self.get_all_pos():
                paned = self.get_paned(pos)
                self._fullscreen_vis[pos] = paned.get_open_pane()
                paned.hide_pane()
                #self.hide_pane(pan)
        else:
             for pos in self.get_all_pos():
                paned = self.get_paned(pos)
                if self._fullscreen_vis.has_key(pos) and \
                    self._fullscreen_vis[pos]:
                    paned.open_pane(self._fullscreen_vis[pos])
        self._fullscreen = fullscreen

    def get_fullscreen(self):
        return self._fullscreen

