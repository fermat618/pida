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

from kiwi.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectControllerMananger, ProjectController, \
    ExecutionActionType, project_action

from pida.ui.views import PidaView
# Some generic project controllers

class GenericExecutionController(ProjectController):

    name = 'GENERIC_EXECUTION'

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandline(
            self.get_option('command_line'),
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

PROJECT_LIST_COLUMNS = [
    Column('markup', use_markup=True)
]

class ProjectListView(PidaView):

    gladefile = 'project_list'

    label_text = 'Projects'

    icon_name = 'package_utilities'

    def create_ui(self):
        self.project_ol.set_headers_visible(False)
        self.project_ol.set_columns(PROJECT_LIST_COLUMNS)

    def on_project_ol__selection_changed(self, ol, project):
        self.svc.set_current_project(project)

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
        )

    def on_project_add(self, action):
        print 'project_add'

class ProjectFeaturesConfig(FeaturesConfig):

    def create_features(self):
        self.create_feature(IProjectController)

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController, GenericExecutionController)


class ProjectCommandsConfig(CommandsConfig):

    def add_directory(self, project_directory):
        self.svc.add_directory(project_directory)

# Service class
class Project(Service):
    """The project manager service"""

    features_config = ProjectFeaturesConfig
    commands_config = ProjectCommandsConfig
    events_config = ProjectEventsConfig
    actions_config = ProjectActionsConfig

    def start(self):
        self._projects = []
        self._project = None
        self._manager = ProjectControllerMananger(self.boss)
        for controller_type in self.features(IProjectController):
            self._manager.register_controller(controller_type)

        ###
        self.project_list = ProjectListView(self)
        self.boss._window.add_view('Buffer', self.project_list)

    def add_directory(self, project_directory):
        # Add a directory to the project list
        for name in os.listdir(project_directory):
            if name.endswith('.pidaproject'):
                project = self._load_project(os.path.join(project_directory, name))
                self.set_current_project(project)
                break

    def set_current_project(self, project):
        self._project = project
        self.emit('project_switched', project=project)

    def _load_project(self, project_file):
        project = self._manager.create_project(project_file)
        self._projects.append(project)
        self.project_list.project_ol.append(project)
        return project


# Required Service attribute for service loading
Service = Project



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
