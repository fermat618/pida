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




# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeatureConfig
from pida.core.interfaces import IProjectController

class GenericExecutionController(ProjectController):

    name = 'GENERIC_EXECUTION'

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandline(
            self.get_option('command_line'),
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )


class ProjectFeatureConfig(FeatureConfig):

    def create_features(self):
        self.create_feature(IProjectController)

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', GenericExecutionController)

# Service class
class Project(Service):
    """The project manager service"""

    features_config = ProjectFeatureConfig

    def start(self):

# Required Service attribute for service loading
Service = Project



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
