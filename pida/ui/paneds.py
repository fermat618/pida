# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import gtk
import gobject

# Don't import moo twice from different locations when the full editor is
# being used.
try:
    import moo
    from moo.utils import BigPaned, PaneLabel, PaneParams, Paned, Pane
    from moo.utils import PANE_POS_BOTTOM, PANE_POS_TOP, PANE_POS_RIGHT, PANE_POS_LEFT
    version = moo.version.split('.')
    if ((int(version[0]) > 0) or
        ((int(version[1]) > 8) and (int(version[2]) > 0)) or
        (int(version[1]) > 9)):
        use_old = False
    else:
        use_old = True

except ImportError:
    from pida.ui.moo_stub import BigPaned, PaneLabel, PaneParams, Paned, Pane
    from pida.ui.moo_stub import PANE_POS_BOTTOM, PANE_POS_TOP, PANE_POS_RIGHT, PANE_POS_LEFT
    use_old = False

from pygtkhelpers.utils import gsignal
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

    gsignal('pane-attachment-changed', gobject.TYPE_PYOBJECT, bool)

    def __init__(self):
        BigPaned.__init__(self)
        self._fullscreen = False
        self._fullscreen_vis = {}
        self.set_property('enable-detaching', True)
        self.set_name('PidaBigPaned')
        for paned in self.get_all_paneds(True):
            paned.connect('notify::active-pane', self._active_pane_change)

    @staticmethod
    def _active_pane_change(paned, dummy):
        """
        Remembers the last active pane
        """
        if paned and paned.props.active_pane:
            paned.last_pane = paned.props.active_pane.weak_ref()

    def get_all_pos(self, every=False):
        if every:
            return [PANE_POS_TOP, PANE_POS_BOTTOM, PANE_POS_LEFT, PANE_POS_RIGHT]
        return [PANE_POS_TOP, PANE_POS_LEFT, PANE_POS_RIGHT]

    def get_all_paneds(self, every=False):
        for pos in self.get_all_pos(every):
            yield self.get_paned(pos)

    def _on_pane_param_changed(self, pane, props):
        """
        we save the detached param and send a clean signal so
        services can do stuff when windows are de/attached
        """
        if pane._was_detached != pane.get_params().detached:
            self.emit('pane-attachment-changed', pane, pane.get_params().detached)
            pane._was_detached = pane.get_params().detached
            if pane.get_params().detached:
                pane.get_child().get_toplevel().connect('focus-in-event',
                                                        self._on_focus_detached,
                                                        pane)

    def _on_focus_detached(self, widget, direction, pane):
        paned = self.get_paned_of_pane(pane)
        if paned:
            paned.last_pane = pane.weak_ref()

    def get_paned_of_pane(self, pane):
        """
        Returns the paned of a pane. There is no dirct api :(
        """
        for paned in self.get_all_paneds(True):
            if pane in paned.list_panes():
                return paned

    def add_view(self, name, view, removable=True, present=True, detachable=True):
        if name == PANE_EDITOR:
            self.add_child(view.get_toplevel())
        else:
            POS = POS_MAP[name]
            lab = PaneLabel(view.icon_name, None, view.label_text)
            if use_old:
                pane = self.insert_pane(view.get_toplevel(), lab, POS, POS)
            else:
                pane = view.key and self.lookup_pane(view.key) or None
                if pane:
                    # we will get a key collission if we dont remove first
                    self.remove_view(pane.view)

                pane = self.insert_pane(view.get_toplevel(), view.key, lab, POS, POS)

            pane.props.detachable = detachable
            #self.set_params(pane, keep_on_top=True)
            view.pane = pane
            pane._was_detached = False
            pane.connect('notify::params', self._on_pane_param_changed)
            pane.view = view
            if not removable:
                pane.set_property('removable', False)
            view._on_remove_attempt_id = pane.connect('remove', 
                                                      view.on_remove_attempt)
            view.toplevel.parent.set_name('PidaWindow')
            if present:
                gcall(self.present_pane, view.get_toplevel())
            self.show_all()

    def __contains__(self, item):
        if not isinstance(item, Pane):
            item = item.pane
        for paned in self.get_all_paneds(True):
            for pane in paned.list_panes():
                if pane == item:
                    return True
        return False

    def remove_view(self, view):
        # remove the default handler and fire the remove handler
        # this ensures the remove event is fired at least once
        if view.pane:
            view.pane.disconnect(view._on_remove_attempt_id)
            view.pane.emit('remove')
        self.remove_pane(view.get_toplevel())
        view.pane = None

    def detach_view(self, view, size=(400,300)):
        paned, pos = self.find_pane(view.get_toplevel())
        dparam = PaneParams(keep_on_top=True, detached=True)
        paned.set_params(dparam)
        paned.detach()
        self._center_on_parent(view, size)

    def present_view(self, view):
        pane, pos = self.find_pane(view.get_toplevel())
        pane.present()


    def list_panes(self, every=False):
        for paned in self.get_all_paneds(every):
            for pane in paned.list_panes():
                yield pane.view

    def get_open_pane(self, name):
        POS = POS_MAP[name]
        paned = self.get_paned(POS)
        pane = None
        if self.get_toplevel().is_active():
            pane = paned.get_open_pane()
        else:
            # we don't have the focus which means that a detached window
            # may have it.
            for pane2 in paned.list_panes():
                if pane2.get_params().detached and \
                   pane2.get_child().get_toplevel().is_active():
                    return paned, pane2
        return paned, pane

    def present_pane_if_not_focused(self, pane):
        """
        Present a pane if it (means any child) does not have the focus
        
        Returns True if the pane was presented
        """
        # test if it is detached
        if pane.get_params().detached:
            if not pane.view.toplevel.get_toplevel().is_active():
                pane.view.toplevel.get_toplevel().present()
                return True
            else:
                return False
        
        # most top focus candidate
        if getattr(pane.view, 'focus_ignore', False):
            return False
        focus = pane.view.toplevel.get_focus_child()
        while hasattr(focus, 'get_focus_child'):
            # we dive into the children until we find a child that has focus
            # or does not have a child
            if focus.is_focus():
                break
            focus = focus.get_focus_child()
        if not focus or not focus.is_focus():
            pane.present()
            return True
        return False

    @staticmethod
    def set_params(pane, **kwargs):
        """
        Updates the parameters on a pane.
        Keyword arguments can be one of the following:
        
        @keep_on_top: sets the sticky flag
        @detached: sets if the window is detached from the main window
        @window_position: position of the pane in detached mode
        @maximized: ???
        """
        oparam = pane.get_params()
        #OMFG don't look at this, 
        # but changing the params does not work for keep_on_top
        try:
            mbuttons = pane.get_child().get_parent().get_parent().\
                            get_children()[0].get_children()
            if len(mbuttons) == 5 and isinstance(mbuttons[2], gtk.ToggleButton):
                # only click works...
                is_top = mbuttons[2].get_active()
            elif len(mbuttons) == 3 and isinstance(mbuttons[1], gtk.ToggleButton):
                # only click works...
                is_top = mbuttons[1].get_active()
            else:
                is_top = oparam.keep_on_top

            if kwargs.get('keep_on_top', None) is not None and \
               is_top != kwargs['keep_on_top']:
                if len(mbuttons) == 5 and isinstance(mbuttons[2], gtk.ToggleButton):
                    # only click works...
                    mbuttons[2].clicked()
                elif len(mbuttons) == 3 and isinstance(mbuttons[1], gtk.ToggleButton):
                    # only click works...
                    mbuttons[1].clicked()
                is_top = not is_top

        except Exception:
            # who knows...
            #import traceback
            #traceback.print_exc()
            mbuttons = None
            is_top = oparam.keep_on_top

        nparam = PaneParams(keep_on_top=is_top, 
                            detached=kwargs.get('detached', oparam.detached),
                            window_position=kwargs.get('window_position', oparam.window_position),
                            maximized=kwargs.get('maximized', oparam.maximized))
        pane.set_params(nparam)

    def get_focus_pane(self):
        if self.get_toplevel().is_active():
            last_pane = getattr(self, 'focus_child', None)
            if not isinstance(last_pane, Paned):
                return
            while True:
                child_pane = getattr(last_pane, 'focus_child', None)
                if isinstance(child_pane, Paned):
                    last_pane = child_pane
                else:
                    return last_pane.get_open_pane()
        else:
            # we don't have the focus which means that a detached window
            # may have it.
            for view in self.list_panes(True):
                if view.pane.get_params().detached and \
                   view.pane.get_child().get_toplevel().is_active():
                    return view.pane


    def switch_next_pane(self, name, needs_focus=True):
        return self._switch_pane(name, 1, needs_focus)

    def switch_prev_pane(self, name, needs_focus=True):
        return self._switch_pane(name, -1, needs_focus)

    def _switch_pane(self, name, direction, needs_focus):
        paned, pane = self.get_open_pane(name)

        if not paned.n_panes():
            # return on empty panes
            return

        def ensure_focus(pane):
            # make sure the pane is in a window which is active
            if pane and not pane.get_child().get_toplevel().is_active():
                pane.get_child().get_toplevel().present()
            return pane

        if hasattr(paned, 'last_pane'):
            last_pane = paned.last_pane() #it's a weak ref
            if last_pane and last_pane.get_params().detached:
                if not last_pane.get_child().get_toplevel().is_active() and needs_focus:
                    last_pane.present()
                    return ensure_focus(last_pane)
            elif last_pane and not pane:
                last_pane.present()
                return ensure_focus(last_pane)

        if needs_focus and pane and self.present_pane_if_not_focused(pane):
            return ensure_focus(pane)

        num = 0
        if pane:
            num = pane.get_index()
        newnum = num + direction

        if newnum == paned.n_panes():
            newnum = 0
        elif newnum < 0:
            newnum = paned.n_panes()-1

        newpane = paned.get_nth_pane(newnum)
        if newpane is None:
            # no pane exists
            return
        paned.last_pane = newpane.weak_ref()
        newpane.present()
        return ensure_focus(newpane)

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
        try:
            px, py, pw, ph, pbd = view.svc.window.window.get_geometry()
        except AttributeError:
            # this can fail if the window is not yet realized, so skip the 
            # the renice stuff :-(
            return
        w, h = size
        cx = (pw - w) / 2
        cy = (ph - h) / 2
        gdkwindow.move_resize(cx, cy, w, h)
        #gdkwindow.resize(w, h)

    def set_fullscreen(self, fullscreen):
        if self._fullscreen == fullscreen:
            return
        if fullscreen:
            for pos in self.get_all_pos():
                paned = self.get_paned(pos)
                self._fullscreen_vis[pos] = {
                     'pane': paned.get_open_pane(),
                     'sticky': paned.props.sticky_pane
                     }
                paned.set_sticky_pane(False)
                paned.props.sticky_pane = False
                paned.hide_pane()
        else:
             for pos in self.get_all_pos(True):
                paned = self.get_paned(pos)
                if pos in self._fullscreen_vis and \
                    self._fullscreen_vis[pos]['pane']:
                    paned.open_pane(self._fullscreen_vis[pos]['pane'])
                    paned.set_sticky_pane(self._fullscreen_vis[pos]['sticky'])
        self._fullscreen = fullscreen

    def get_fullscreen(self):
        return self._fullscreen

    def is_visible_pane(self, pane):
        """
        Test if a pane is visible to the user or not
        """
        # detached are always visible
        if not pane:
            return False
        if pane.get_params().detached:
            return True
        # this is kinda tricky because the widgets think they are visible
        # even when they are in a non top pane
        for paned in self.get_all_paneds(True):
            if pane == paned.get_open_pane():
                return True
        return False

