# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
from gtk import gdk
from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input
from kiwi.ui.views import BaseView
from kiwi.ui.delegates import GladeDelegate

from pida.ui.uimanager import PidaUIManager
from pida.ui.paneds import PidaPaned

from pida.core.log import log
from pida.core.environment import get_uidef_path, get_pixmap_path
from pida.core.actions import accelerator_group
from pida.utils.gthreads import gcall

from functools import wraps

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

def with_gdk_lock(func):
    @wraps(func)
    def _wrapped(*k, **kw):
        try:
            gdk.threads_enter()
            func(*k, **kw)
        finally:
            gdk.threads_leave()
    return _wrapped
        
class Window(gtk.Window):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        gtk.Window.__init__(self, *args, **kw)
        self.set_icon_from_file(get_pixmap_path('pida-icon.png'))
        self.add_accel_group(accelerator_group)
        self.connect('delete-event', self._on_delete_event)
        self.create_all()

    def _on_delete_event(self, window, event):
        return not self._boss.stop()

    def create_all(self):
        pass

    # Dialogs
    def save_dlg(self, *args, **kw):
        return save(parent = self, *args, **kw)

    def open_dlg(self, *args, **kw):
        return opendlg(parent = self, *args, **kw)

    def info_dlg(self, *args, **kw):
        return info(parent = self, *args, **kw)

    @with_gdk_lock
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
    def add_view(self, paned, view, removable=True, present=False, detachable=True):
        self.paned.add_view(paned, view, removable, present, detachable=detachable)

    def remove_view(self, view):
        self.paned.remove_view(view)

    def detach_view(self, view, size):
        self.paned.detach_view(view, size)

    def present_view(self, view):
        self.paned.present_view(view)

    def present_paned(self, bookname):
        self.paned.present_paned(bookname)

    def switch_next_view(self, bookname):
        self.paned.switch_next_pane(bookname)

    def switch_prev_view(self, bookname):
        self.paned.switch_prev_pane(bookname)

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


class WorkspaceWindow(GladeDelegate):
    gladefile = 'workspace_select'
    
    class Entry(object):
        id = 0
        pid = 0
        status = None
        workspace = None
        project = None
        open_files = 0

    def __init__(self, command=None):
        """
        The WorkspaceWindow is displayed whenever the user should choose a 
        workspace to run.
        
        @fire_command: dbus command to send to an already running 
        @command: run command when one workspace is choosen
        @spawn_new: on the default handle. spawn a new process
        """
        #self.set_role('workspace') 
        #self.set_name('Pidaworkspace')

        self.workspaces = []
        self.command = command
        self.list_complete = False
        self.new_workspace = ""
        self.user_action = None

        super(WorkspaceWindow, self).__init__()

        #self.set_role('workspace') 
        self.toplevel.set_name('Pidaworkspace')

        from kiwi.environ import environ
        self.pic_on = gtk.gdk.pixbuf_new_from_file(
                    environ.find_resource('pixmaps', 'online.png'))
        self.pic_off = gtk.gdk.pixbuf_new_from_file(
                    environ.find_resource('pixmaps', 'offline.png'))

        from kiwi.ui.objectlist import Column

        self.workspace_view.set_columns([
            Column('id', visible=False),
            Column('pid', visible=False),
            Column('status', title=' ', width=30, data_type=gtk.gdk.Pixbuf, expand=False, expander=False),
            Column('workspace', title=_('Workspace'), searchable=True, sorted=True, expand=True),
            Column('project', title=_('Project'), expand=True),
            Column('open_files', title=_('Open Files'), data_type=int),
        ])

        gcall(self.update_workspaces)

    def _rcv_pida_workspace(self, *args):
        # this is the callback from the dbus signal call
        import dbus
        # list: busname, pid, on/off pic, workspace, project, open files
        # args:  uid, pid, workspace, project, opened_files
        if len(args) > 4 and not isinstance(args[0], dbus.lowlevel.ErrorMessage):
            for row in self.workspace_view:
                if row.workspace == args[2]:
                    row.id = args[0]
                    row.pid = args[1]
                    row.status = self.pic_on
                    row.workspace = args[2]
                    row.project = args[3]
                    row.open_files = args[4]
            self.workspace_view.refresh()
        elif len(args) and isinstance(args[0], dbus.lowlevel.ErrorMessage):
            self.list_complete = True

    def update_workspaces(self):
        from pida.utils.pdbus import list_pida_instances, PidaRemote
    
        from pida.core.options import OptionsManager, list_workspaces
        from pida.core import environment
        # we need a new optionsmanager so the default manager does not workspace
        # lookup yet
        self.list_complete = False
        lst = list_workspaces()
        # start the dbus message so we will know which ones are running
        list_pida_instances(callback=self._rcv_pida_workspace)

        self.workspace_view.clear()
        select = None
        for workspace in lst:

            pid = 0
            # we could find this things out of the config
            project = ""
            count = 0

            entry = self.Entry()
            entry.id = ""
            entry.pid = pid
            entry.status = self.pic_off
            entry.workspace = workspace
            entry.project = project
            entry.open_files = count
            
            if entry.workspace == "default":
                select = entry

            self.workspace_view.append(entry)
        if select:
            self.workspace_view.select(select)
            self.workspace_view.grab_focus()

    def on_workspace_view__row_activated(self, widget, obj):
        self.user_action = "select"

        self.new_workspace = obj.workspace

        if self.command:
            self.command(self, obj)


    def on_new_workspace__clicked(self, widget):
        # ask for new workspace name
        self.user_action = "new"
        from pida.ui.gtkforms import DialogOptions, create_gtk_dialog
        opts = DialogOptions().add('name', label=_("Workspace name"), value="")
        create_gtk_dialog(opts, parent=self.toplevel).run()
        if opts.name and self.command:
            self.new_workspace = opts.name
            self.command(self)

    def on_use_workspace__clicked(self, widget):
        self.on_workspace_view__row_activated(widget, 
                                              self.workspace_view.get_selected())

    def on_UseWorkspace__activate(self, widget):
        self.on_workspace_view__row_activated(widget,
                                              self.workspace_view.get_selected())

    def on_DelWorkspace__activate(self, *args, **kwargs):
        opt = self.workspace_view.get_selected()
        if opt.id:
            error(_("You can't delete a running workspace"))
        else:
            if yesno(
              _('Do you really want to delete workspace %s ?') %opt.workspace,
                parent = self.toplevel) == gtk.RESPONSE_YES:
                from pida.core.options import OptionsManager
                OptionsManager.delete_workspace(opt.workspace)
                self.workspace_view.remove(opt)

    def _create_popup(self, event, *actions):
        menu = gtk.Menu()
        for act in actions:
            if act is not None:
                mi = act.create_menu_item()
            else:
                mi = gtk.SeparatorMenuItem()
            menu.add(mi)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def on_workspace_view__right_click(self, ol, target, event):
        self._create_popup(event, self.UseWorkspace, None, self.DelWorkspace)

    def on_quit__clicked(self, *args):
        self.on_workspace_select__close()

    def on_workspace_select__close(self, *args):
        self.user_action = "quit"
        if self.command:
            self.command(self)
