import gtk

from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input

from pida.ui.uimanager import PidaUIManager
from pida.ui.paneds import PidaPaned

from pida.core.environment import get_uidef_path, get_pixmap_path
from pida.core.actions import accelerator_group


class Window(gtk.Window):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        gtk.Window.__init__(self, *args, **kw)
        self.set_icon_from_file(get_pixmap_path('pida-icon.png'))
        self.add_accel_group(accelerator_group)
        self.connect('delete-event', self._on_delete_event)
        self.create_all()
        self.show()

    def _on_delete_event(self, window, event):
        if self.yesno_dlg('Are you sure you want to exit?'):
            self._boss.stop()
        else:
            return True

    def create_all(self):
        pass

    # Dialogs
    def save_dlg(self, *args, **kw):
        return save(parent = self, *args, **kw)

    def open_dlg(self, *args, **kw):
        return opendlg(parent = self, *args, **kw)

    def info_dlg(self, *args, **kw):
        return info(parent = self, *args, **kw)

    def error_dlg(self, *args, **kw):
        return error(parent = self, *args, **kw)

    def yesno_dlg(self, *args, **kw):
        return yesno(parent = self, *args, **kw) == gtk.RESPONSE_YES

    def error_list_dlg(self, msg, errs):
        return self.error_dlg('%s\n\n* %s' % (msg, '\n\n* '.join(errs)))

    def input_dlg(self, *args, **kw):
        return get_input(parent=self, *args, **kw)


class PidaWindow(Window):

    """Main PIDA Window"""


    def create_all(self):
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
        self.main_box.pack_start(self.top_box, expand=False)
        self.main_box.pack_start(self._paned)
        self.main_box.pack_start(self.bottom_box, expand=False)
        self.add(self.main_box)
        
    def _start_ui(self):
        self._menubar = self._uim.get_menubar()
        self._toolbar = self._uim.get_toolbar()
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.top_box.pack_start(self._menubar, expand=False)
        self.top_box.pack_start(self._toolbar, expand=False)
        self.top_box.show_all()
        self.main_box.show_all()

    def _fix_paneds(self):
        self._paned = PidaPaned()

    # Action group API
    def add_action_group(self, actiongroup):
        self._uim.add_action_group(actiongroup)

    def add_uidef(self, filename):
        try:
            uifile = get_uidef_path(filename)
            self._uim.add_ui_from_file(uifile)
        except Exception, e:
            print 'unable to get %s resource' % filename

    # View API
    def add_view(self, bookname, view, present=False):
        self._paned.add_view(bookname, view, present)

    def remove_view(self, view):
        self._paned.remove_view(view)

    def detach_view(self, view, size):
        self._paned.detach_view(view, size)

    def present_view(self, view):
        self._paned.present_view(view)

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

