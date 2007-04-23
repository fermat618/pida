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


# Service class
class Versioncontrol(Service):
    """The Versioncontrol service"""

    features_config = VersioncontrolFeaturesConfig

    
    def ignored_file_checker(self, path, name, state):
        return not ( state == "hidden" or state == "ignored")
    
    def list_files(self, path):
        workdir = None
        for vcm in self.features("workdir-manager"):
            try:
                workdir = vcm(path)
                break
            except ValueError:
                continue
        
        if workdir is not None: 
            for item in workdir.list(paths=[path]):
                abspath = item.abspath
                name = os.path.basename (abspath)
                path = os.path.dirname(abspath)
                yield name, path, item.state



# Required Service attribute for service loading
Service = Versioncontrol



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
