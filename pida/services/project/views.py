

from pygtkhelpers.ui.objectlist import Column
from pygtkhelpers.ui.widgets import AttrSortCombo

from pida.utils.puilder.view import PuilderView

from pida.ui.views import PidaView

from .project import _, locale

def format_project(proj):
    return '<b>%s</b>\n%s' % (proj.display_name, proj.source_directory)


class ProjectListView(PidaView):

    key = 'project.list'

    builder_file = 'project_list'
    locale = locale
    label_text = _('Projects')

    icon_name = 'package_utilities'


    def create_ui(self):
        self.project_ol.set_columns([
            Column(title='Ignored',
                   use_markup=True,
                   format_func=format_project)
        ])
        self._sort_combo = AttrSortCombo(self.project_ol, [
                ('display_name', 'Name'),
                ('source_directory', 'Full Path'),
                ('name', 'Directory Name'),
                ], 'display_name')
        self._sort_combo.show()
        self.main_vbox.pack_start(self._sort_combo, expand=False)

    def on_project_ol__selection_changed(self, ol):
        self.svc.set_current_project(ol.selected_item)

    def on_project_ol__item_activated(self, ol, project):
        self.svc.boss.cmd('filemanager', 'browse', new_path=project.source_directory)
        self.svc.boss.cmd('filemanager', 'present_view')

    def on_project_ol__item_right_clicked(self, ol, project, event):
        self.svc.boss.cmd('contexts', 'popup_menu', context='dir-menu',
            dir_name=project.source_directory, event=event,
            project=project)

    def set_current_project(self, project):
        self.project_ol.selected_item = project

    def update_project(self, project):
        self.project_ol.update(project)

    def remove(self, project):
        # each may be None, we get the desired behavior in all cases
        # desired = if not first item select the one before
        #           else try to select the one after
        #           if empty select none
        before = self.project_ol.item_before(project)
        after = self.project_ol.item_after(project)
        self.project_ol.selected_item = before or after
        self.project_ol.remove(project)

    def can_be_closed(self):
        self.svc.get_action('project_properties').set_active(False)


class ProjectSetupView(PidaView):

    key = 'project.editor'

    label_text = _('Project Properties')

    def create_ui(self):
        self.script_view = PuilderView()
        self.script_view.widget.show() #XXX: why was that here
        self.script_view.set_execute_method(self.test_execute)
        self.script_view.connect('cancel-request',
                                 self._on_script_view__cancel_request)
        self.script_view.connect('project-saved',
                                 self._on_script_view__project_saved)


        self.add_tool('Puilder', self.script_view)

    def add_tool(self, name, widget):
        #XXX: real implementation
        self.add_slave(widget, 'widget')

    def test_execute(self, target, project):
        self.svc.execute_target(None, target, project)

    def set_project(self, project):
        #XXX: should we have more than one project viev ?
        #     for different projects each
        #XXX: ask on case of unsaved changes?
        self.project = project
        #self.script_view.load_script(
        #        os.path.join(
        #            project.source_directory,
        #            'build.vel'
        #            )
        #        )
        self.script_view.set_build(project.build)
        self.script_view.set_project(project)

    def _on_script_view__cancel_request(self, script_view):
        self.svc.get_action('project_properties').set_active(False)

    def _on_script_view__project_saved(self, script_view, project):
        # reload the project when it gets saved
        if self.svc._current is project:
            self.svc.update_execution_menus()

    def can_be_closed(self):
        self.svc.get_action('project_properties').set_active(False)
