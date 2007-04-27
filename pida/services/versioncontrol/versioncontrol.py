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


import os.path

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

class VersioncontrolFeaturesConfig(FeaturesConfig):
    
    def create_features(self):
        self.create_feature("workdir-manager")
    
    def subscribe_foreign_features(self):
        from pida.utils.anyvc import all_known

        for mgr in all_known:
            self.subscribe_feature("workdir-manager", mgr)

        self.subscribe_foreign_feature(
                "filemanager", "file_lister",
                self.svc.list_files
                )
        self.subscribe_foreign_feature(
                "filemanager", "file_hidden_check",
                self.svc.ignored_file_checker
                )
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'versioncontrol-file-menu.xml'))

class VersionControlEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
            self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.get_action('differences').set_sensitive(document is not None)

class VersioncontrolCommandsConfig(CommandsConfig):
    
    def get_workdirmanager(self,path):
        return self.svc.get_workdir_manager_for_path(path)

class VersionControlActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'differences',
            TYPE_NORMAL,
            'Differences',
            'Version Control differences for the current file',
            '',
            self.on_diff,
            '<Shift><Control>d',
        )

        self.create_action(
            'more_vc_for_file_menu',
            TYPE_NORMAL,
            'More Version Control',
            'More Version Control Commands',
            '',
            lambda *a: None,
            'NOACCEL'
        )

        self.create_action(
            'diff_for_file',
            TYPE_NORMAL,
            'Differences',
            'Get the version controll diff on this file',
            '',
            self.on_diff_for_file,
            'NOACCEL',
        )

    def on_diff(self, action):
        document = self.svc.boss.cmd('buffer', 'get_current')
        self.svc.diff_document(document)

    def on_diff_for_file(self, action):
        file_name = action.contexts_kw['file_name']
        self.svc.diff_file(file_name)

# Service class
class Versioncontrol(Service):
    """The Versioncontrol service"""

    features_config = VersioncontrolFeaturesConfig
    commands_config = VersioncontrolCommandsConfig
    actions_config = VersionControlActions
    events_config = VersionControlEvents

    def start(self):
        self.get_action('differences').set_sensitive(False)
    
    def ignored_file_checker(self, path, name, state):
        return not ( state == "hidden" or state == "ignored")
   
    def get_workdir_manager_for_path(self, path):
        for vcm in self.features("workdir-manager"):
            try:
                return vcm(path) #TODO: this shouldnt need an exception
            except ValueError:
                pass

    def list_files(self, path):
        workdir = self.get_workdir_manager_for_path(path)

        if workdir is not None: 
            for item in workdir.list(paths=[path]):
                abspath = item.abspath
                name = os.path.basename (abspath)
                path = os.path.dirname(abspath)
                yield name, path, item.state

    def diff_document(self, document):
        self.diff_file(document.filename)

    def diff_file(self, file_name):
        vc = self.get_workdir_manager_for_path(file_name)
        commandargs = vc.diff() + [file_name]
        cwd = vc.base_path
        self.boss.cmd('commander', 'execute', commandargs=commandargs, cwd=cwd)




# Required Service attribute for service loading
Service = Versioncontrol



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
