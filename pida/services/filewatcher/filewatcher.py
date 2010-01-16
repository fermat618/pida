# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gobject
import os

from os.path import exists, isdir, isfile

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig

# locale
from pida.core.locale import Locale
locale = Locale('filewatcher')
_ = locale.gettext

import gio

class FilewatcherEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('filemanager', 'browsed_path_changed',
                               self.svc.on_browsed_path_changed)

class FileWatcherOptions(OptionsConfig):

    def create_options(self):
        self.create_option(
            'enable_filemon',
            _('Enable FileMonitor'),
            bool,
            False,
            _('Whether FileMonitor will be enabled'),
            self.on_enabled_changed,
            safe=False
        )

    def on_enabled_changed(self, option):
        if option.value:
            self.svc.start_giofilemon()
        else:
            self.svc.stop_giofilemon()

# Service class
class FileWatcher(Service):
    """the pyinotify File watcher service"""

    events_config = FilewatcherEvents
    options_config = FileWatcherOptions

    def callcmd(self, cmd, name):

        self.boss.cmd('filemanager', command,
                filename=os.path.basename(name),
                dirname=self.dir)

    def add_path(self, path):
        if path is None or not exists(path):
            return
        f = gio.File(path)
        if isdir(path):
            monitor=f.monitor_directory( gio.FILE_MONITOR_NONE)
        elif isfile(path):
            monitor=f.monitor_file(gio.FILE_MONITOR_NONE)
        else:
            return #XXX: unknown type?
        monitor.connect("changed", self.on_changed)
        self.monitors[path] = monitor


    def on_changed(self, mon, file, otherfile, event): 
        #print file, otherfile, event

        # ['FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED', 'FILE_MONITOR_EVENT_CHANGED', 'FILE_MONITOR_EVENT_CHANGES_DONE_HINT', 'FILE_MONITOR_EVENT_CREATED', 'FILE_MONITOR_EVENT_DELETED', 'FILE_MONITOR_EVENT_PRE_UNMOUNT', 'FILE_MONITOR_EVENT_UNMOUNTED', 'FILE_MONITOR_NONE', 'FILE_MONITOR_WATCH_MOUNTS']
        #XXX: store events, act on hints
        if event in (gio.FILE_MONITOR_EVENT_DELETED,):
            self.callcmd('update_removed_file', file.get_path())
        elif event in (gio.FILE_MONITOR_EVENT_CHANGED,
                       gio.FILE_MONITOR_EVENT_CREATED,
                       gio.FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED):
            self.callcmd('update_file', file.get_path())

        
    def pre_start(self):
        self.monitors = {}
        self.dir = None
        self.started = False

    def start(self):
        if self.opt('enable_filemon'):
            self.start_giofilemon()

    def start_giofilemon(self):
            self.started = True
            #gtk.main() #start
            #gobject.timeout_add(1000, self._period_check)
    
    def stop_giofilemon(self):
        self.started = False
        self.monitors.clear()
        
    def stop(self):
        self.stop_giofilemon()


    def on_browsed_path_changed(self, path):
        self.set_directory(path)
    
    def stop_watch(self, path):
        del self.monitors[path]


    def set_directory(self, dir):
        # stop watching old directory
        if self.dir is not None and self.dir != dir:
            self.stop_watch(self.dir)
            self.add_path(dir)
        # setting new directory
            self.dir = dir






# Required Service attribute for service loading

Service = FileWatcher


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
