import gtk

from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input
from kiwi.ui.views import BaseView

from pida.ui.uimanager import PidaUIManager
from pida.ui.paneds import PidaPaned

from pida.core.log import log
from pida.core.environment import get_uidef_path, get_pixmap_path
from pida.core.actions import accelerator_group

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class Window(gtk.Window):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        gtk.Window.__init__(self, *args, **kw)
        self.set_icon_from_file(get_pixmap_path('pida-icon.png'))
        self.add_accel_group(accelerator_group)
        self.connect('delete-event', self._on_delete_event)
        self.create_all()

    def _on_delete_event(self, window, event):
        return self._boss.stop()

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
        self.main_box.pack_start(self._paned)
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
        self._paned = PidaPaned()

    # Action group API
    def add_action_group(self, actiongroup):
        self._uim.add_action_group(actiongroup)

    def add_uidef(self, filename):
        try:
            uifile = get_uidef_path(filename)
            return self._uim.add_ui_from_file(uifile)
        except Exception, e:
            log.debug('unable to get %s resource: %s' %
                                (filename, e))

    def remove_action_group(self, actiongroup):
        self._uim.remove_action_group(actiongroup)

    def remove_uidef(self, ui_merge_id):
        if ui_merge_id is not None:
            self._uim.remove_ui(ui_merge_id)

    # View API
    def add_view(self, paned, view, removable=True, present=False):
        self._paned.add_view(paned, view, removable, present)

    def remove_view(self, view):
        self._paned.remove_view(view)

    def detach_view(self, view, size):
        self._paned.detach_view(view, size)

    def present_view(self, view):
        self._paned.present_view(view)

    def present_paned(self, bookname):
        self._paned.present_paned(bookname)

    def switch_next_view(self, bookname):
        self._paned.switch_next_pane(bookname)

    def switch_prev_view(self, bookname):
        self._paned.switch_prev_pane(bookname)

    def get_statusbar(self):
        return self._statusbar

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

from kiwi.ui.delegates import GladeDelegate
class SessionWindow(BaseView):
    gladefile = 'session_select'

    def __init__(self, sessions=None, fire_command=None, spawn_new=None):

        self.sessions = sessions
        self._fire_command = fire_command
        self._spawn_new = spawn_new
        self.new_session = ""

        BaseView.__init__(self) #, delete_handler=quit_if_last)
        sigs = {
            'on_window_delete_event': self.on_quit,
            'on_new_session_clicked': self.on_new_session_clicked,
            'on_use_session_clicked': self.on_use_session_clicked,
            'gtk_main_quit': self.on_quit,
            'on_session_view_row_activated': self.on_session_view_row_activated,
        }
        self._glade_adaptor.signal_autoconnect(sigs)
        self.session_list = gtk.ListStore(str, str, str, str, int)
        self.session_view.set_model(self.session_list)
        cell = gtk.CellRendererText()
        cell.set_property('xalign', 1.0)
        self.session_view.append_column(gtk.TreeViewColumn(_('PID'), cell, text=1))
        self.session_view.append_column(gtk.TreeViewColumn(_('Session'), cell, text=2))
        self.session_view.append_column(gtk.TreeViewColumn(_('Project'), cell, text=3))
        self.session_view.append_column(gtk.TreeViewColumn(_('Open'), cell, text=4))
        #tvc.set_min_width(titles[n][1])

        self.update_sessions()
        #self.add_proxy(self.model, self.widgets)

    def update_sessions(self):
        from pida.utils.pdbus import list_pida_instances, PidaRemote

        if not self.sessions:
            self.sessions = list_pida_instances()

        self.session_list.clear()
        for s in self.sessions:
            pr = PidaRemote(s)
            try:    pid = pr.call('boss', 'get_pid')
            except: pid = "<error>"
            try:    session = pr.call('sessions', 'get_session_name')
            except: session = "default"
            try:    project = pr.call('project', 'get_current_project_name')
            except: project = "<error>"
            try:    count = pr.call('buffer', 'get_open_documents_count')
            except: count = 0
            self.session_list.append((s, pid, session, project, count))

    def on_session_view_row_activated(self, widget, num, col):
        if not self._fire_command:
            return

        from pida.utils.pdbus import PidaRemote

        row = self.session_list[num]
        pr = PidaRemote(row[0])
        pr.call(*self._fire_command[0], **self._fire_command[1])

        self.on_quit()

    def on_new_session_clicked(self, widget):
        # ask for new session name
        from pida.ui.gtkforms import DialogOptions, create_gtk_dialog
        opts = DialogOptions().add('name', label=_("Session name"), value="")
        create_gtk_dialog(opts, parent=self.toplevel).run()
        if opts.name and callable(self._spawn_new):
            self.new_session = opts.name
            self._spawn_new(self)

    def on_use_session_clicked(self, widget):
        num = self.session_view.get_selection().get_selected_rows()[1][0][0]
        self.on_session_view_row_activated(widget, num, None)

    def on_quit(self, *args):
        gtk.main_quit()
