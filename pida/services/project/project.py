# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import os

import gtk

from configobj import ConfigObj

from kiwi.ui.objectlist import Column
# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, \
    TYPE_TOGGLE
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectControllerMananger, ProjectController, \
    ProjectKeyDefinition

from pida.ui.views import PidaGladeView


def open_directory_dialog(parent, title, folder=''):
    filechooser = gtk.FileChooserDialog(title,
                                        parent,
                                        gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    filechooser.set_default_response(gtk.RESPONSE_OK)

    if folder:
        filechooser.set_current_folder(folder)

    response = filechooser.run()
    if response != gtk.RESPONSE_OK:
        filechooser.destroy()
        return

    path = filechooser.get_filename()
    if path and os.access(path, os.R_OK):
        filechooser.destroy()
        return path


# Some generic project controllers

class GenericExecutionController(ProjectController):

    name = 'GENERIC_EXECUTION'

    label = 'Generic Execution'

    attributes = [
        ProjectKeyDefinition('command', 'Execution Command', True),
    ] + ProjectController.attributes

    def execute(self):
        command = self.get_option('command')
        if not command:
            self.boss.get_window().error_dlg(
                'Controller has no command set'
            )
            return
        env = self.get_option('env')
        if env:
            env = env.split()
        else:
            env = []
        self.execute_commandline(
            command,
            self.get_option('cwd') or self.project.source_directory,
            env,
        )

PROJECT_LIST_COLUMNS = [
    Column('markup', use_markup=True)
]

class ProjectListView(PidaGladeView):

    gladefile = 'project_list'

    label_text = 'Projects'

    icon_name = 'package_utilities'

    def create_ui(self):
        self.project_ol.set_headers_visible(False)
        self.project_ol.set_columns(PROJECT_LIST_COLUMNS)

    def on_project_ol__selection_changed(self, ol, project):
        self.svc.set_current_project(project)

    def on_project_ol__double_click(self, ol, project):
        self.svc.boss.cmd('filemanager', 'browse', new_path=project.source_directory)

class ProjectPropertiesView(PidaGladeView):

    gladefile = 'project-properties'

    def create_ui(self):
        self.controllers_list.set_columns([
            Column('markup', use_markup=True, expand=True, title='Controllers'),
            Column('default', radio=True, data_type=bool, editable=True)
        ])
        self.items_list.set_columns([
            Column('label', title='Name', expand=True, use_markup=True),
            Column('value', editable=True, expand=True),
        ])
        self._project = None

    def set_project(self, project):
        self._project = project
        self.controllers_list.clear()
        self.project_label.set_text('')
        if self._project is not None:
            self.project_label.set_markup(self._project.markup)
            for controller in self._project.controllers:
                self.controllers_list.append(controller)

    def on_controllers_list__selection_changed(self, ol, controller):
        self.items_list.clear()
        if controller is not None:
            for item in controller.create_key_items():
                self.items_list.append(item)
        self.delete_button.set_sensitive(controller is not None)

    def set_controllers(self, controllers):
        self.controllers_combo.prefill([(controller.label, controller) for
            controller in controllers])

    def on_add_button__clicked(self, button):
        name = self.name_entry.get_text()
        if not name:
            self.svc.boss.get_window().error_dlg(
                'Please enter a controller name')
            return
        for controller in self._project.controllers:
            if controller.config_section == name:
                self.svc.boss.get_window().error_dlg(
                    'This project already has a controller named %s' % name)
                return
        self.name_entry.set_text('')
        controller_type = self.controllers_combo.read()
        controller = self._project.add_controller(controller_type, name)
        self.controllers_list.append(controller, select=True)
        self.svc.set_current_project(self._project)

    def on_delete_button__clicked(self, button):
        controller = self.controllers_list.get_selected()
        if controller is not None:
            if self.svc.boss.get_window().yesno_dlg(
            'Are you sure you want to delete controller "%s" from this project?'
            % controller.config_section):
                self._project.remove_controller(controller)
                self.controllers_list.remove(controller)
                self.svc.set_current_project(self._project)


class ProjectEventsConfig(EventsConfig):

    def create_events(self):
        self.create_event('project_switched')

class ProjectActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'project_add',
            TYPE_NORMAL,
            'New Project',
            'Creates a new project',
            gtk.STOCK_NEW,
            self.on_project_add,
        )

        self.create_action(
            'project_execute',
            TYPE_MENUTOOL,
            'Execute Project',
            'Execute the project',
            gtk.STOCK_EXECUTE,
            self.on_project_execute,
        )

        self.create_action(
            'project_remove',
            TYPE_NORMAL,
            'Remove from workspace',
            'Remove the current project from the workspace',
            gtk.STOCK_DELETE,
            self.on_project_remove,
        )

        self.create_action(
            'project_properties',
            TYPE_TOGGLE,
            'Project Properties',
            'Show the project property editor',
            'settings',
            self.on_project_properties,
        )

    def on_project_remove(self, action):
            self.svc.remove_current_project()

    def on_project_add(self, action):
        path = open_directory_dialog(
            self.svc.boss.get_window(),
            'Select a directory to add'
        )
        if path:
            self.svc.cmd('add_directory', project_directory=path)

    def on_project_execute(self, action):
        controller = self.svc.get_default_controller()
        if controller is None:
            controllers = self.svc.get_controllers()
            if controllers:
                controller = controllers[0]
        if controller is not None:
            controller.execute()
        else:
            self.svc.boss.get_window().error_dlg(
                'This project has no controllers')

    def on_project_properties(self, action):
        self.svc.show_properties(action.get_active())

class ProjectFeaturesConfig(FeaturesConfig):

    def create_features(self):
        self.create_feature(IProjectController)

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController, GenericExecutionController)


class ProjectCommandsConfig(CommandsConfig):

    def add_directory(self, project_directory):
        self.svc.add_directory(project_directory)

    def get_view(self):
        return self.svc.get_view()

# Service class
class Project(Service):
    """The project manager service"""

    features_config = ProjectFeaturesConfig
    commands_config = ProjectCommandsConfig
    events_config = ProjectEventsConfig
    actions_config = ProjectActionsConfig

    def pre_start(self):
        self._projects = []
        self.set_current_project(None)
        self._manager = ProjectControllerMananger(self.boss)
        for controller_type in self.features(IProjectController):
            self._manager.register_controller(controller_type)

        ###
        self.project_list = ProjectListView(self)
        self.project_properties_view = ProjectPropertiesView(self)
        self.project_properties_view.set_controllers(self.features(IProjectController))
        self._read_workspace_file()

    def _read_workspace_file(self):
        self._workspace_file = os.path.join(self.boss.get_pida_home(), 'projects.conf')
        if os.path.exists(self._workspace_file):
            f = open(self._workspace_file)
            for line in f:
                dirname = line.strip()
                path = os.path.join(line.strip(),
                    '%s.pidaproject' % os.path.basename(dirname))
                if os.path.exists(path):
                    self._load_project(path)
                else:
                    self.log_warn('Project path %s has disappeared' % path)
            f.close()

    def _save_workspace_file(self):
        f = open(self._workspace_file, 'w')
        for project in self._projects:
            f.write('%s\n' % project.source_directory)
        f.close()

    def get_view(self):
        return self.project_list

    def add_directory(self, project_directory):
        # Add a directory to the project list
        for name in os.listdir(project_directory):
            if name.endswith('.pidaproject'):
                project = self.load_and_set_project(os.path.join(project_directory, name))
                self._save_workspace_file()
                return project
        if self.boss.get_window().yesno_dlg(
            'The directory does not contain a project file, do you want to '
            'create one?'
        ):
            self.create_project_file(project_directory)
            self._save_workspace_file()

    def create_project_file(self, project_directory):
        project_name = os.path.basename(project_directory)
        file_name = '%s.pidaproject' % project_name
        path = os.path.join(project_directory, file_name)
        self._create_blank_project_file(project_name, path)
        self.load_and_set_project(path)

    def _create_blank_project_file(self, name, file_path):
        config = ConfigObj(file_path)
        config['name'] = name
        config.write()

    def set_current_project(self, project):
        self._project = project
        self.get_action('project_remove').set_sensitive(project is not None)
        self.get_action('project_execute').set_sensitive(project is not None)
        self.get_action('project_properties').set_sensitive(project is not None)
        if project is not None:
            self.project_properties_view.set_project(project)
            self.emit('project_switched', project=project)
            toolitem = self.get_action('project_execute').get_proxies()[0]
            toolitem.set_menu(self.create_menu())

    def load_and_set_project(self, project_file):
        project = self._load_project(project_file)
        self.set_current_project(project)

    def _load_project(self, project_file):
        project = self._manager.create_project(project_file)
        self._projects.append(project)
        self.project_list.project_ol.append(project)
        return project

    def remove_current_project(self):
        self.remove_project(self._project)

    def remove_project(self, project):
        self._projects.remove(project)
        self.project_list.project_ol.remove(project, select=True)
        self._save_workspace_file()

    def get_default_controller(self):
        if self._project is not None:
            return self._project.get_default_controller()
   
    def get_controllers(self):
        if self._project is not None:
            return self._project.controllers()

    def create_menu(self):
        if self._project is not None:
            menu = gtk.Menu()
            for controller in self._project.controllers:
                def _callback(act, controller):
                    controller.execute()
                act = gtk.Action(controller.config_section,
                    controller.config_section,
                    controller.execute.im_func.func_doc, '')
                act.connect('activate', _callback, controller)
                mi = act.create_menu_item()
                menu.add(mi)
            menu.show_all()
            return menu

    def show_properties(self, visible):
        if visible:
            self.boss.cmd('window', 'add_view', paned='Plugin',
                view=self.project_properties_view)
        else:
            self.boss.cmd('window', 'remove_view',
                view=self.project_properties_view)



# Required Service attribute for service loading
Service = Project



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
