import os
import gtk
from pygtkhelpers.delegates import ToplevelView
from pygtkhelpers.ui import dialogs
from pygtkhelpers.ui.objectlist import Column
from pida.ui.window import _
from pygtkhelpers.gthreads import gcall


class WorkspaceWindow(ToplevelView):
    builder_file = 'workspace_select'

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
        self.widget.set_name('Pidaworkspace')
        
        import pida #XXX: not zip save
        base = os.path.join(pida.__path__[0], 'resources', 'pixmaps')
        self.pic_on = gtk.gdk.pixbuf_new_from_file(
                    os.path.join(base, 'online.png'))
        self.pic_off = gtk.gdk.pixbuf_new_from_file(
                    os.path.join(base, 'offline.png'))


        self.workspace_view.set_columns([
            Column('id', visible=False),
            Column('pid', visible=False),
            Column('status', title=' ', width=30, type=gtk.gdk.Pixbuf), #, expand=False, expander=False),
            Column('workspace', title=_('Workspace'),),# searchable=True, sorted=True, expand=True),
            Column('project', title=_('Project'), expand=True),
            Column('open_files', title=_('Open Files'), type=int),
        ])

        gcall(self.update_workspaces)

    def update_workspaces(self):
        from pida.utils.pdbus import list_pida_instances
        from pida.core.options import list_workspaces

        self.list_complete = False

        workspaces = list_workspaces()
        instances = list_pida_instances()

        self.workspace_view.clear()
        select = None

        for workspace in workspaces:

            pid = 0
            # we could find this things out of the config
            project = ""
            count = 0

            entry = self.Entry()

            entry.workspace = workspace
            current_instances = [x for x in instances if x['workspace'] == workspace]
            if current_instances:
                #XXX: aggregate ?!
                entry.pid = current_instances[0]['pid']
                entry.status = self.pic_on
                entry.project = current_instances[0]['project']
                entry.open_files = len(current_instances[0]['buffers'])
            else:
                entry.pid = 0
                entry.status = self.pic_off
                entry.project = ''
                entry.open_files = 0

            if workspace == "default":
                select = entry

            self.workspace_view.append(entry)
        if select:
            self.workspace_view.selected_item = select
            self.workspace_view.grab_focus()

    def _use_workspace(self, item):
        self.user_action = "select"
        self.new_workspace = item.workspace
        if self.command:
            self.command(self, item)

    def _use_selected_workspace(self):
        self._use_workspace(self.workspace_view.selected_item)

    def on_workspace_view__item_activated(self, widget, item):
        self._use_workspace(item)

    def on_new_workspace__clicked(self, widget):
        # ask for new workspace name
        self.user_action = "new"
        name = dialogs.input('Workspace name', label='Workspace Name')
        if name is not None and self.command:
            self.new_workspace = name
            self.command(self)

    def on_use_workspace__clicked(self, widget):
        self._use_selected_workspace()

    def on_UseWorkspace__activate(self, widget):
        self._use_selected_workspace()

    def on_DelWorkspace__activate(self, *args, **kwargs):
        opt = self.workspace_view.get_selected()
        if opt.id:
            dialogs.error(_("You can't delete a running workspace"))
        else:
            if dialogs.yesno(
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

    def on_workspace_view__item_right_clicked(self, ol, target, event):
        self._create_popup(event, self.UseWorkspace, None, self.DelWorkspace)

    def on_quit__clicked(self, *args):
        self.on_workspace_select__close()

    def on_workspace_select__close(self, *args):
        self.user_action = "quit"
        if self.command:
            self.command(self)
