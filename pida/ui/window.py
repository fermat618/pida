# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import pkgutil
import gtk
from gtk import gdk
import os

from pygtkhelpers.ui import dialogs

from pida.ui.uimanager import PidaUIManager
from pida.ui.paneds import PidaPaned

from pida.core.log import log
from pida.core.actions import accelerator_group, global_accelerator_group

from functools import wraps

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

def with_gdk_lock(func):
    @wraps(func)
    def _wrapped(*k, **kw):
        with gdk.lock:
            func(*k, **kw)
    return _wrapped

def with_gdk_leave(func):
    @wraps(func)
    def _wrapped(*k, **kw):
        try:
            func(*k, **kw)
        finally:
            gdk.threads_leave()
    return _wrapped

class Window(gtk.Window):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        gtk.Window.__init__(self, *args, **kw)
        self.set_icon_from_file(os.path.join(
            os.path.dirname(__file__),
            '../resources/pixmaps/pida-icon.png'))
        self.add_accel_group(accelerator_group)
        self.add_accel_group(global_accelerator_group)
        self.connect('delete-event', self._on_delete_event)
        self.create_all()

    def _on_delete_event(self, window, event):
        return not self._boss.stop()

    def create_all(self):
        pass

    # Dialogs
    def save_dlg(self, *args, **kw):
        return dialogs.save(parent = self, *args, **kw)

    def open_dlg(self, *args, **kw):
        return dialogs.open(parent = self, *args, **kw)

    @with_gdk_leave
    def info_dlg(self, *args, **kw):
        return dialogs.info(parent = self, *args, **kw)

    @with_gdk_leave
    def error_dlg(self, *args, **kw):
        return dialogs.error(parent = self, *args, **kw)

    def yesno_dlg(self, *args, **kw):
        return dialogs.yesno(parent = self, *args, **kw) == gtk.RESPONSE_YES

    @with_gdk_leave
    def error_list_dlg(self, msg, errs):
        return self.error_dlg('%s\n\n* %s' % (msg, '\n\n* '.join(errs)))

    @with_gdk_leave
    def input_dlg(self, *args, **kw):
        return dialogs.input(parent=self, *args, **kw)


class PidaWindow(Window):

    """Main PIDA Window"""


    def create_all(self):
        self.set_role('Main')
        self.set_name('PidaMain')
        self.set_title(_('PIDA Loves You!'))
        self._fix_paneds()
        self._create_ui()
        self.resize(800, 600)

    def start(self):
        self._start_ui()

    def _create_ui(self):
        self._uim = PidaUIManager()
        self.main_box = gtk.VBox()
        self.top_box = gtk.VBox()
        self.bottom_box = gtk.VBox()
        self._create_statusbar()
        self.main_box.pack_start(self.top_box, expand=False)
        self.main_box.pack_start(self.paned)
        self.main_box.pack_start(self.bottom_box, expand=False)
        self.main_box.pack_start(self._status_holder, expand=False)
        self.add(self.main_box)

    def _create_statusbar(self):
        self._statusbar = gtk.HBox()
        self._status_holder = gtk.Statusbar()
        # OMG
        frame = self._status_holder.get_children()[0]
        frame.remove(frame.get_children()[0])
        frame.add(self._statusbar)

    def _start_ui(self):
        self._menubar = self._uim.get_menubar()
        self._toolbar = self._uim.get_toolbar()
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.top_box.pack_start(self._menubar, expand=False)
        self.top_box.pack_start(self._toolbar, expand=False)
        self.top_box.show_all()
        self.main_box.show_all()
        self._statusbar.show_all()

    def _fix_paneds(self):
        self.paned = PidaPaned()

    # Action group API
    def add_action_group(self, actiongroup):
        self._uim.add_action_group(actiongroup)

    def add_uidef(self, package, path):
        try:
            content = pkgutil.get_data(package, path)
            return self._uim.add_ui_from_string(content)
        except Exception, e:
            log.debug('unable to get %s: %r resource: %s' %
                                (package, path, e))

    def remove_action_group(self, actiongroup):
        self._uim.remove_action_group(actiongroup)

    def remove_uidef(self, ui_merge_id):
        if ui_merge_id is not None:
            self._uim.remove_ui(ui_merge_id)

    # View API
    def add_view(self, paned, view, removable=True, present=False, detachable=True):
        self.paned.add_view(paned, view, removable, present, detachable=detachable)

    def get_focus_pane(self):
        return self.paned.get_focus_pane()

    def remove_view(self, view):
        self.paned.remove_view(view)

    def detach_view(self, view, size):
        self.paned.detach_view(view, size)

    def present_view(self, view):
        self.paned.present_view(view)

    def present_paned(self, bookname):
        self.paned.present_paned(bookname)

    def switch_next_view(self, bookname):
        return self.paned.switch_next_pane(bookname)

    def switch_prev_view(self, bookname):
        return self.paned.switch_prev_pane(bookname)

    def set_fullscreen(self, fullscreen):
        self.paned.set_fullscreen(fullscreen)

    def get_fullscreen(self):
        return self.paned.get_fullscreen()

    def get_statusbar(self):
        return self._statusbar

    def create_merge_id(self):
        return self._uim._uim.new_merge_id()

    # UI hiding API
    def set_toolbar_visibility(self, visibility):
        if visibility:
            self._toolbar.show_all()
        else:
            self._toolbar.hide_all()

    def set_menubar_visibility(self, visibility):
        if visibility:
            self._menubar.show_all()
        else:
            self._menubar.hide_all()

    def set_statusbar_visibility(self, visibility):
        if visibility:
            self._statusbar.show_all()
        else:
            self._statusbar.hide_all()

    def __contains__(self, item):
        return self.paned.__contains__(item)

