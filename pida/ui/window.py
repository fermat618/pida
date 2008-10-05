import gtk

from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input
from kiwi.ui.views import BaseView

from pida.ui.uimanager import PidaUIManager
from pida.ui.paneds import PidaPaned

from pida.core.log import log
from pida.core.environment import get_uidef_path, get_pixmap_path
from pida.core.actions import accelerator_group
from pida.utils.gthreads import gcall

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

    def set_fullscreen(self, fullscreen):
        self._paned.set_fullscreen(fullscreen)

    def get_fullscreen(self):
        return self._paned.get_fullscreen()

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

    def __init__(self, command=None):
        """
        The SessionWindow is displayed whenever the user should choose a 
        session to run.
        
        @fire_command: dbus command to send to an already running 
        @command: run command when one session is choosen
        @spawn_new: on the default handle. spawn a new process
        """

        self.sessions = []
        self.command = command
        self.list_complete = False
        #self._spawn_command = spawn_command
        #self._fire_command = fire_command
        #self._spawn_new = spawn_new
        self.new_session = ""
        self.user_action = None

        BaseView.__init__(self) #, delete_handler=quit_if_last)
        sigs = {
            'on_window_delete_event': self.on_quit,
            'on_new_session_clicked': self.on_new_session_clicked,
            'on_use_session_clicked': self.on_use_session_clicked,
            'on_session_view_popup_menu': self.on_session_view_popup_menu,
            'gtk_main_quit': self.on_quit,
            'on_session_view_row_activated': self.on_session_view_row_activated,
        }

        from kiwi.environ import environ
        self.pic_on = gtk.gdk.pixbuf_new_from_file(
                    environ.find_resource('pixmaps', 'online.png'))
        self.pic_off = gtk.gdk.pixbuf_new_from_file(
                    environ.find_resource('pixmaps', 'offline.png'))


        self._glade_adaptor.signal_autoconnect(sigs)
        # busname, pid, on/off pic, session, project, open files
        self.session_list = gtk.ListStore(str, int, gtk.gdk.Pixbuf, str, str, int)
        self.session_view.set_model(self.session_list)
        cell = gtk.CellRendererText()
        cell.set_property('xalign', 1.0)
        pcell = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('', pcell, pixbuf=2)
        col.set_spacing(40)
        self.session_view.append_column(col)
        col = gtk.TreeViewColumn(_('Session'), cell, text=3)
        col.set_spacing(5)
        col.set_resizable(True) 
        self.session_view.append_column(col)
        col = gtk.TreeViewColumn(_('Project'), cell, text=4)
        col.set_spacing(5)
        col.set_resizable(True)
        self.session_view.append_column(col)
        col = gtk.TreeViewColumn(_('Open files'), cell, text=5)
        col.set_spacing(5)
        col.set_resizable(True)
        self.session_view.append_column(col)
        self.session_view.append_column(gtk.TreeViewColumn('', gtk.CellRendererText()))
        #tvc.set_min_width(titles[n][1])

        #self.update_sessions()
        gcall(self.update_sessions)
        #self.add_proxy(self.model, self.widgets)

    def _rcv_pida_session(self, *args):
        # this is the callback from the dbus signal call
        import dbus
        # list: busname, pid, on/off pic, session, project, open files
        # args:  uid, pid, session, project, opened_files
        if len(args) > 4 and not isinstance(args[0], dbus.lowlevel.ErrorMessage):
            for row in self.session_list:
                if row[3] == args[2]:
                    row[0] = args[0]
                    row[1] = args[1]
                    row[2] = self.pic_on
                    row[3] = args[2]
                    row[4] = args[3]
        elif len(args) and isinstance(args[0], dbus.lowlevel.ErrorMessage):
            self.list_complete = True

    def update_sessions(self):
        from pida.utils.pdbus import list_pida_instances, PidaRemote
    
        from pida.core.options import OptionsManager
        from pida.core import environment
        # we need a new optionsmanager so the default manager does not session
        # lookup yet
        self.list_complete = False
        om = OptionsManager(session="default")

        lst = om.list_sessions()
        #if not self.sessions:
        #    print "list"
        # start the dbus message so we will know which ones are running
        list_pida_instances(callback=self._rcv_pida_session)

        self.session_list.clear()
        for session in lst:

            pid = 0
            # we could find this things out of the config
            project = ""
            count = 0

            self.session_list.append(("", pid, self.pic_off, session, project, count))

    def on_session_view_row_activated(self, widget, num, col):
        self.user_action = "select"
        row = self.session_list[num]

        self.new_session = row[1]

        if self.command:
            self.command(self, row)


    def on_new_session_clicked(self, widget):
        # ask for new session name
        self.user_action = "new"
        from pida.ui.gtkforms import DialogOptions, create_gtk_dialog
        opts = DialogOptions().add('name', label=_("Session name"), value="")
        create_gtk_dialog(opts, parent=self.toplevel).run()
        if opts.name and self.command:
            self.new_session = opts.name
            self.command(self)

    def on_use_session_clicked(self, widget):
        num = self.session_view.get_selection().get_selected_rows()[1][0][0]
        self.on_session_view_row_activated(widget, num, None)

    def on_session_view_popup_menu(self, widget):
        print "popup"
        self.list_menu.popup(None, None, None, 0, 0, None)

    def on_menu_delete_session_activate(self, *args, **kwargs):
        print "delete", args, kwargs

    def on_quit(self, *args):
        self.user_action = "quit"
        if self.command:
            self.command(self)
        #self.hide_and_quit()
