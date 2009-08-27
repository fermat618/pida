# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gobject

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

have_gio, have_gamin, have_pyinotify=False, False, False
try:
    import gio
    have_gio=True
except ImportError:
    try:
        import gamin
        have_gamin = True
    except ImportError:
        have_gamin = False
        try:
            import pyinotify
            from pyinotify import Notifier, WatchManager, ProcessEvent, IN_DELETE, IN_MODIFY, IN_CREATE, IN_MOVED_FROM, IN_MOVED_TO
            have_pyinotify=True
        except:
            have_pyinotify=False
        

class FileWatcherService(Service):
    
    def start(self): raise NotImplementedError
    def stop(self): raise NotImplementedError
    
    
class FilewatcherEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('filemanager', 'browsed_path_changed',
                               self.svc.on_browsed_path_changed)

if have_gio:
    class GIOFileWatcherOptions(OptionsConfig):

        def create_options(self):
            self.create_option(
                'enable_giofilemon',
                _('Enable GIOFileMonitor'),
                bool,
                False,
                _('Whether GIOFileMonitor wil be enabled'),
                self.on_enabled_changed,
                safe=False
            )

        def on_enabled_changed(self, option):
            if option.value:
                self.svc.start_giofilemon()
            else:
                self.svc.stop_giofilemon()

    # Service class
    class GIOFileWatcher(Service):
        """the pyinotify File watcher service"""

        events_config = FilewatcherEvents
        options_config = GIOFileWatcherOptions
        
            
        def callcmd(self, cmd, name):
                self._callback(cmd, name)
                
        def _callback(self, command, name):
                    self.boss.cmd('filemanager', command, filename=name,
                        dirname=self.dir)
                        
        class GIOFileMonitor(object):
    
            def __init__(self, outer, path=None):
                    self.outer=outer
                    self.monitors = {}
                    self.add_path(path)
            
            def add_path(self, path):
                if path is None: return
                if exists(path):
                    monitor = None
                    f=gio.File(path)
                    if isdir(path):
                        monitor=f.monitor_directory( gio.FILE_MONITOR_NONE)
                    elif isfile(path):
                        monitor=f.monitor_file(gio.FILE_MONITOR_NONE)
                    
                    if monitor is not None:
                        monitor.connect("changed", self.on_changed)
                        self.monitors[path] = monitor

            def remove_path(self, path):
                del self.monitors[path]
                
            def on_changed(self, mon, file, otherfile, event): 
                #print file, otherfile, event

                #['FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED', 'FILE_MONITOR_EVENT_CHANGED', 'FILE_MONITOR_EVENT_CHANGES_DONE_HINT', 'FILE_MONITOR_EVENT_CREATED', 'FILE_MONITOR_EVENT_DELETED', 'FILE_MONITOR_EVENT_PRE_UNMOUNT', 'FILE_MONITOR_EVENT_UNMOUNTED', 'FILE_MONITOR_NONE', 'FILE_MONITOR_WATCH_MOUNTS']
                if event in [gio.FILE_MONITOR_EVENT_DELETED]:
                    self.outer.callcmd('update_removed_file', file.get_path())
                elif event in [gio.FILE_MONITOR_EVENT_CHANGED, gio.FILE_MONITOR_EVENT_CREATED]:
                    self.outer.callcmd('update_file', file.get_path())

            
        def pre_start(self):
            self.dir = None
            self.started = False
            self.giofilemon= None
            self.cache = []
            if have_gio:
                self.giofilemon=self.GIOFileMonitor(self)

        def start(self):
            if self.giofilemon and self.opt('enable_giofilemon'):
                self.start_giofilemon()

        def start_giofilemon(self):
            if have_gio:
                self.started = True
                #gtk.main() #start
                #gobject.timeout_add(1000, self._period_check)
        
        def stop_giofilemon(self):
            self.started=False
            
        def stop(self):
            self.stop_giofilemon()
            self.giofilemon = None

        def stop_pyinotify(self):
            self.started = False

        def on_browsed_path_changed(self, path):
            self.set_directory(path)
        
        def stop_watch(self, path):
            if self.giofilemon is not None:
                self.giofilemon.remove_path(path)
            
        def set_directory(self, dir):
            if self.giofilemon is not None:
                self.giofilemon.add_path(dir)

            # stop watching old directory
            if self.dir is not None and self.dir != dir:
                self.stop_watch(self.dir)

            # setting new directory
            self.dir = dir
            #self.gamin.watch_directory(self.dir, self._callback)
            #self.notifier=Notifier(self.watchmanager, self.PDir())
            


elif have_gamin:

    class GaminFileWatcherOptions(OptionsConfig):

        def create_options(self):
            self.create_option(
                'enable_gamin',
                _('Enable Gamin'),
                bool,
                False,
                _('Whether Gamin wil be enabled'),
                self.on_enabled_changed,
                safe=False
            )

        def on_enabled_changed(self, option):
            if option.value:
                self.svc.start_gamin()
            else:
                self.svc.stop_gamin()


    # Service class


    class GaminFilewatcher(Service):
        """the Gamin File watcher service"""

        events_config = FilewatcherEvents
        options_config = GaminFileWatcherOptions

        def pre_start(self):
            self.dir = None
            self.started = False
            self.gamin = None
            self.cache = []
            if have_gamin:
                self.gamin = gamin.WatchMonitor()
                self.gamin.no_exists()

        def start(self):
            if self.gamin and self.opt('enable_gamin'):
                self.start_gamin()

        def start_gamin(self):
            if have_gamin:
                self.started = True
                gobject.timeout_add(1000, self._period_check)

        def stop(self):
            self.stop_gamin()
            self.gamin = None

        def stop_gamin(self):
            self.started = False

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

            # don't send many time the same event
            if [name, event] in self.cache:
                return
            self.cache.append([name, event])


            if event == gamin.GAMChanged or event == gamin.GAMCreated:
                command = 'update_file'
            elif event == gamin.GAMDeleted or event == gamin.GAMMoved:
                command = 'update_removed_file'
            else:
                command = None
            if command:
                self.boss.cmd('filemanager', command, filename=name,
                    dirname=self.dir)

        def _period_check(self):
            if not self.started:
                return False
            self.cache = []
            self.gamin.handle_events()
            return True

elif have_pyinotify:
    
    class PyINotifyFileWatcherOptions(OptionsConfig):

        def create_options(self):
            self.create_option(
                'enable_pyinotify',
                _('Enable pyinotify'),
                bool,
                False,
                _('Whether pyinotify wil be enabled'),
                self.on_enabled_changed,
                safe=False
            )

        def on_enabled_changed(self, option):
            if option.value:
                self.svc.start_pyinotify()
            else:
                self.svc.stop_pyinotify()

    # Service class
    class PyINotifyFileWatcher(Service):
        """the pyinotify File watcher service"""

        events_config = FilewatcherEvents
        options_config = PyINotifyFileWatcherOptions
        
        
        def _callback(self, cmd, name):
                self.boss.cmd('filemanager', command, filename=name,
                    dirname=self.dir)
        callcmd=_callback
        
        class PDir(ProcessEvent):
            def my_init(self, outer, **kwargs):
                self.outer=outer
                self.mv_cookies={} #{cookie: src}
            
            def process_IN_DELETE(self, event):
                self._callback('update_removed_file', event.pathname)
                
            def process_IN_CREATE(self, event):
                self._callback('update_file', event.pathname)
                
            def process_IN_MODIFY(self, event):
                self._callback('update_file', event.pathname)
                   
            def process_IN_MOVED_FROM(self, event):
                self._callback('update_removed_file', event.pathname)
                
            def process_IN_MOVED_TO(self, event):
                self._callback('update_removed_file', event.pathname)
                

            
        def pre_start(self):
            self.dir = None
            self.started = False
            self.pyinotify = None
            self.cache = []
            if have_pyinotify:
                self.watchmanager=WatchManager()
                self.mask=IN_DELETE|IN_CREATE|IN_MOVED_FROM|IN_MOVED_TO|IN_MODIFY
                #self.gamin = gamin.WatchMonitor()
                #self.gamin.no_exists()

        def start(self):
            if self.pyinotify and self.opt('enable_pyinotify'):
                self.start_pyinotify()

        def start_pyinotify(self):
            if have_pyinotify:
                self.started = True
                self.notifier=Notifier(self.watchmanager, self.PDir())
                #gobject.timeout_add(1000, self._period_check)

        def stop(self):
            self.stop_pyinotify()
            self.pyinotify = None

        def stop_pyinotify(self):
            self.started = False

        def on_browsed_path_changed(self, path):
            self.set_directory(path)
        
        def stop_watch(self, path):
            self.watchmanager.rm_watch(path)
            
        def set_directory(self, dir):
            if not self.pyinotify:
                self.dir = dir
                self.watchmanager.add_watch(self.dir, self.mask) #, rec=True)
                return

            # stop watching old directory
            if self.dir is not None and self.dir != dir:
                self.stop_watch(self.dir)

            # setting new directory
            self.dir = dir
            #self.gamin.watch_directory(self.dir, self._callback)
            #self.notifier=Notifier(self.watchmanager, self.PDir())
            

        #def _period_check(self):
            #if not self.started:
                #return False
            #self.cache = []
            #self.gamin.handle_events()
            #return True


def watcher_factory():
    if have_gio:
        return GIOFileWatcher
    elif have_gamin:
        return GaminFilewatcher
    elif have_pyinotify:
        return PyINotifyFilewatcher
    else:
        raise Exception("[-]GIO/Gamin/pyinotify")
# Required Service attribute for service loading

Service = watcher_factory()


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
