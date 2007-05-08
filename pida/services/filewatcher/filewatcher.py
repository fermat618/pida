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

import gobject

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig

try:
    import gamin
    have_gamin = True
except ImportError:
    have_gamin = False

class FilewatcherEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('filemanager', 'browsed_path_changed',
                                     self.svc.on_browsed_path_changed)

# Service class
class Filewatcher(Service):
    """the File watcher service"""

    events_config = FilewatcherEvents

    def pre_start(self):
        self.dir = None
        self.started = False
        self.gamin = None
        if have_gamin:
            self.gamin = gamin.WatchMonitor()
            self.gamin.no_exists()

    def start(self):
        if self.gamin:
            gobject.timeout_add(1000, self._period_check)

    def stop(self):
        if self.started and self.gamin:
            self.gamin.stop_watch()
        self.started = False
        self.gamin = None

    def on_browsed_path_changed(self, path):
        self.set_directory(path)

    def set_directory(self, dir):
        if not self.gamin:
            self.dir = dir
            return

        # stop watching old directory
        if self.dir is not None and self.dir != dir:
            self.gamin.stop_watch(self.dir)

        # setting new directory
        self.dir = dir
        self.gamin.watch_directory(self.dir, self._callback)

    def _callback(self, name, event):
        if event == gamin.GAMAcknowledge:
            return
        if event == gamin.GAMChanged or event == gamin.GAMCreated:
            # XXX HIDDEN FILES EVIL
            if name.startswith('.'):
                command = None
            # XXX DARCS EVIL
            elif name == ('darcs_testing_for_nfs' or
                (name.startswith('darcs') and len(name) == 11)):
                command = None
            else:
                command = 'update_file'
        elif event == gamin.GAMDeleted:
            command = 'update_removed_file'
        else:
            command = None
        if command:
            self.boss.cmd('filemanager', command, filename=name,
                dirname=self.dir)

    def _period_check(self):
        if not self.gamin:
            return False
        self.gamin.handle_events()
        return True


# Required Service attribute for service loading
Service = Filewatcher



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
