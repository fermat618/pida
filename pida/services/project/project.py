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

from pida.utils.configobj import ConfigObj

from kiwi.ui.objectlist import Column
# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.options import OptionsConfig, OTypeStringList, OTypeFile
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, \
    TYPE_TOGGLE
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectControllerMananger, ProjectController, \
    ProjectKeyDefinition

from pida.ui.views import PidaGladeView

# locale
from pida.core.locale import Locale
locale = Locale('project')
_ = locale.gettext


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

    label = _('Generic Execution')

    attributes = [
        ProjectKeyDefinition('command', _('Execution Command'), True),
    ] + ProjectController.attributes

    def execute(self):
        command = self.get_option('command')
        if not command:
            self.boss.get_window().error_dlg(
                _('Controller has no command set')
            )
            return
        self.execute_commandline(
            command,
        )

PROJECT_LIST_COLUMNS = [
    Column('markup', use_markup=True)
]

class ProjectListView(PidaGladeView):

    gladefile = 'project_list'
    locale = locale
    label_text = _('Projects')

    icon_name = 'package_utilities'

    def create_ui(self):
        self.project_ol.set_headers_visible(False)
        self.project_ol.set_columns(PROJECT_LIST_COLUMNS)

    def on_project_ol__selection_changed(self, ol, project):
        self.svc.set_current_project(project)

    def on_project_ol__double_click(self, ol, project):
        self.svc.boss.cmd('filemanager', 'browse', new_path=project.source_directory)
        self.svc.boss.cmd('filemanager', 'present_view')

    def on_project_ol__right_click(self, ol, project, event):
        self.svc.boss.cmd('contexts', 'popup_menu', context='dir-menu',
                          dir_name=project.source_directory, event=event)

    def set_current_project(self, project):
        self.project_ol.select(project)

class ProjectPropertiesView(PidaGladeView):

    gladefile = 'project-properties'
    locale = locale
    label_text = _('Project Properties')

    icon_name = 'package_utilities'

    def create_ui(self):
        self.controllers_list.set_columns([
            Column('markup', use_markup=True, expand=True, title=_('Controllers')),
            Column('default', radio=True, data_type=bool, editable=True, title=_('Defaut'))
        ])
        self.items_list.set_columns([
            Column('label', title=_('Name'), expand=True, use_markup=True),
            Column('value', title=_('Value'), editable=True, expand=True),
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
                _('Please enter a controller name'))
            return
        for controller in self._project.controllers:
            if controller.config_section == name:
                self.svc.boss.get_window().error_dlg(
                    _('This project already has a controller named %s') % name)
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
            _('Are you sure you want to delete controller "%s" from this project?')
            % controller.config_section):
                self.controllers_list.remove(controller)
                self._project.remove_controller(controller)
                self.svc.set_current_project(self._project)

    def on_close_button__clicked(self, button):
        self.svc.get_action('project_properties').set_active(False)


class ProjectEventsConfig(EventsConfig):

    def create_events(self):
        self.create_event('project_switched')

class ProjectActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'project_add',
            TYPE_NORMAL,
            _('Add Project'),
            _('Adds a new project'),
            gtk.STOCK_ADD,
            self.on_project_add,
        )

        self.create_action(
            'project_execute',
            TYPE_MENUTOOL,
            _('Execute Default'),
            _('Execute the project'),
            'package_utilities',
            self.on_project_execute,
        )

        self.create_action(
            'project_remove',
            TYPE_NORMAL,
            _('Remove from workspace'),
            _('Remove the current project from the workspace'),
            gtk.STOCK_DELETE,
            self.on_project_remove,
        )

        self.create_action(
            'project_properties',
            TYPE_TOGGLE,
            _('Project Properties'),
            _('Show the project property editor'),
            'settings',
            self.on_project_properties,
        )

        self.create_action(
            'project_execution_menu',
            TYPE_NORMAL,
            _('Execution Controllers'),
            _('Configurations with which to execute the project'),
            gtk.STOCK_EXECUTE,
            self.on_project_execution_menu,
        )

    def on_project_remove(self, action):
        self.svc.remove_current_project()

    def on_project_add(self, action):
        path = open_directory_dialog(
            self.svc.boss.get_window(),
            _('Select a directory to add')
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
                _('This project has no controllers'))

    def on_project_properties(self, action):
        self.svc.show_properties(action.get_active())

    def on_project_execution_menu(self, action):
        menuitem = action.get_proxies()[0]
        menuitem.remove_submenu()
        menuitem.set_submenu(self.svc.create_menu())

class ProjectFeaturesConfig(FeaturesConfig):

    def create_features(self):
        self.create_feature(IProjectController)

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController, GenericExecutionController)


class ProjectOptions(OptionsConfig):

    def create_options(self):
        self.create_option(
            'project_dirs',
            _('Project Directories'),
            OTypeStringList,
            [],
            _('The current directories in the workspace'),
        )

        self.create_option(
            'last_project',
            _('Last Project'),
            OTypeFile,
            '',
            (_('The last project selected. ') +
            _('(Do not change this unless you know what you are doing)'))
        )



class ProjectCommandsConfig(CommandsConfig):

    def add_directory(self, project_directory):
        self.svc.add_directory(project_directory)

    def get_view(self):
        return self.svc.get_view()

    def get_current_project(self):
        return self.svc.get_current_project()

    def save_to_current_project(self, section_name, section_data):
        self.svc.get_current_project().save_section(section_name, section_data)

    def get_current_project_data(self, section_name):
        return self.svc.get_current_project().get_section(section_name)


# Service class
class Project(Service):
    """The project manager service"""

    features_config = ProjectFeaturesConfig
    commands_config = ProjectCommandsConfig
    events_config = ProjectEventsConfig
    actions_config = ProjectActionsConfig
    options_config = ProjectOptions

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
        self._read_options()

    def start(self):
        last = self.opt('last_project')
        for project in self._projects:
            if last:
                if project.source_directory == last:
                    self.project_list.set_current_project(project)

    def _read_options(self):
        for dirname in self.opt('project_dirs'):
            path = os.path.join(dirname, '%s.pidaproject' %
                                      os.path.basename(dirname))
            if os.path.exists(path):
                project = self._load_project(path)
            else:
                self.log_warn(_('Project path %s has disappeared') % path)

    def _save_options(self):
        self.set_opt('project_dirs',
            [p.source_directory for p in self._projects])

    def get_view(self):
        return self.project_list

    def add_directory(self, project_directory):
        # Add a directory to the project list
        project_file = '%s.pidaproject' % os.path.basename(project_directory)
        for name in os.listdir(project_directory):
            if name == project_file:
                project = self.load_and_set_project(os.path.join(project_directory, name))
                self._save_options()
                return project
        if self.boss.get_window().yesno_dlg(
            _('The directory does not contain a project file, ') +
            _('do you want to create one?')
        ):
            self.create_project_file(project_directory)
            self._save_options()

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
        self.get_action('project_execution_menu').set_sensitive(project is not None)
        if project is not None:
            self.project_properties_view.set_project(project)
            self.emit('project_switched', project=project)
            toolitem = self.get_action('project_execute').get_proxies()[0]
            toolitem.set_menu(self.create_menu())
            self.set_opt('last_project', project.source_directory)
            self.boss.editor.set_path(project.source_directory)


    def get_current_project(self):
        return self._project

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
        if self.boss.get_window().yesno_dlg(
            _('Are you sure you want to remove project "%s" from the workspace?')
            % project.name
        ):
            self._projects.remove(project)
            self.project_list.project_ol.remove(project, select=True)
            self._save_options()

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
                    controller.execute.im_func.func_doc, gtk.STOCK_EXECUTE)
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
