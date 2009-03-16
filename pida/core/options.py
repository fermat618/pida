# -*- coding: utf-8 -*-
"""
    Options Management
    ~~~~~~~~~~~~~~~~~~

    This module handles the storrage of configuration data.
    There are 3 semantical locations of configuration data:
    * global
    * workspace
    * project *todo*


    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
from __future__ import with_statement
from functools import partial
from .base import BaseConfig
from .environment import is_safe_mode, killsettings, settings_dir
from .pdbus import DbusOptionsManager
from pango import Font
from shutil import rmtree
import simplejson


from os import path
import os
get_settings_path = partial(os.path.join, settings_dir)

def add_directory(*parts):
    dirn = get_settings_path(*parts)
    if not os.path.exists(dirn):
        os.makedirs(dirn)
    return dirn

def unset_directory(*parts):
    #XXX: reload=!
    path = get_settings_path(*parts)
    if os.path.exists(path):
        rmtree(get_settings_path(*parts))

def initialize():
    add_directory('keyboard_shortcuts')
    add_directory('workspaces')

def list_workspaces():
    """Returns a list with all workspace names """
    workspaces = get_settings_path('workspaces')
    return [ x for x in os.listdir(workspaces)
                if path.isdir(
                    path.join(workspaces, x)
                )
            ]

class OptionsManager(object):

    def __init__(self, workspace=None):

        initialize()
        self._workspace = None
        if workspace:
            self.workspace = workspace
        if killsettings():
            unset_directory()

    @staticmethod
    def delete_workspace(workspace):
        unset_directory('workspaces', workspace)

    def initialize_workspace(self):
        add_directory('workspaces', self.workspace)

    def open_workspace_manager(self):
        data = {}
        try:
            with open(get_settings_path('appcontroller.json')) as file:
                data = simplejson.load(file)
                return bool(data.get('open_workspace_manager', False))
        except Exception, e:
            return False

    def _set_workspace(self, value):
        self._workspace = value
        self.initialize_workspace()

    def _get_workspace(self):
        if self._workspace is None:
            # we need this form of lazy loading because the default manager
            # is created so early that the workspace name is not known then
            import pida.core.environment
            self._workspace = pida.core.environment.workspace_name()
        return self._workspace

    workspace = property(_get_workspace, _set_workspace)

    def on_change(self, option):
        pass #XXX: implement

class BaseChoice(str): pass

def choices(choices):
    """Helper to generate string options for choices"""
    class Choices(BaseChoice):
        """Option that should be one of the choices"""
        options = choices

    return Choices

class Color(str): """Option which is a color in RGB Hex"""


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc, callback, 
                 workspace=None):
        self.group = group
        self.name = name
        self.label = label
        self.type = rtype
        self.doc = doc
        self.default = default
        self.workspace = bool(workspace)
        self.callback = callback
        self.value = None

    def set_value(self, value):
        if self.group:
            self.group.set_value(self.name, value)
        else:
            self.value = value

    def add_notify(self, callback, *args):
        import warnings
        warnings.warn("deprecated", DeprecationWarning)

    def _get_nlabel(self):
        return self.label.replace("_","",1)

    def __repr__(self):
        return '<OptionItem %s %s:%s>' %(self.group, self.name, self.type)

    no_mnemomic_label = property(_get_nlabel)

class ExtraOptionItem(object):

    def __init__(self, group, path, default, callback, 
                 workspace=False, notify=True, no_submit=False):
        self.group = group
        self.path = path
        # currently only json is supported
        self.type = "json"
        self.default = default
        self.workspace = bool(workspace)
        self.callback = callback
        self.value = None
        self.dirty = True
        self.notfiy = True
        self.no_submit = no_submit

    def set_value(self, value):
        self.value = value
        self.dirty = False

    @property
    def name(self):
        return self.path

    def __repr__(self):
        return '<ExtraOptionItem %s>' %(self.path)


manager = OptionsManager()

class OptionsConfig(BaseConfig, DbusOptionsManager): 

    #enable reuse for keyboard shortcuts that need different name
    name='%s.json'
    dbus_path = "options"

    def __init__(self, service, *args, **kwargs):
        DbusOptionsManager.__init__(self, service)
        BaseConfig.__init__(self, service, *args, **kwargs)

    def create(self):
        self.name = self.__class__.name%self.svc.get_name()
        add_directory('workspaces', manager.workspace)
        self.workspace_path = get_settings_path('workspaces', manager.workspace, self.name)
        self.global_path = get_settings_path(self.name)
        self._options = {}
        self._extra_files = {}
        self._exports = {}
        self.create_options()
        self.register_options()


    def create_options(self) :
        """Create the options here"""

    def register_options(self):
        # in safemode we reset all dangerouse variables so pida can start
        # even if there are some settings + pida bugs that cause problems
        # default values MUST be safe
        for name, value in self.read().items():

            # ignore removed options that might have config entries
            if name in self._options:
                self._options[name].value = value

        if is_safe_mode() and False:#XXX: disabled
            for opt in self:
                if not opt.save:
                    self.set_value(opt.name, opt.default) #XXX: this writes on every change, BAD

        for opt in self:
            if opt.value is None:
                self.set_value(opt.name, opt.default)


    def register_extra_file(self, path, default, callback=None, 
                      safe=True, workspace=False, notify=True):
        """
        Registers an aditional option file a service uses.
        
        The object stored in the extra file is only one object which
        can be serialized by simplejson.
        
        All further accesses to the data object should happen over
        get_extra(name) which will make sure that other pida
        instances have syncronized data.
        
        """
        #XXX: support for project-level files?
        #assert not (workspace and project)
        opt = ExtraOptionItem(self, path, default, callback, workspace,
                              notify=notify)
        self._extra_files[path] = opt
    
    def get_extra(self, name):
        opt = self._extra_files[name]
        if opt.dirty:
            # reread the file
            opt.value = self.read_extra(opt.path, opt.default)
            opt.dirty = False
        
        return opt.value
        
    def save_extra(self, name, data):
        """
        Saves a data object to the extra file name
        """

    def create_option(self, name, label, type, default, doc, callback=None, 
                      safe=True, workspace=False):
        opt = OptionItem(self, name, label, type, default, doc,
                         callback, workspace)
        self.add_option(opt)
        return opt


    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]

    def get_value(self, name):
        return self._options[name].value

    def set_extra_value(self, path, value, dbus_notify=True, save=True):
        option = self._extra_files[path]
        option.set_value(value)
        self._on_change(option, dbus_notify=dbus_notify)
        if save:
            self.dump_data(option.path, option.value)

    def set_value(self, name, value, dbus_notify=True, save=True):
        option = self._options[name]
        option.value = value
        self._on_change(option, dbus_notify=dbus_notify)
        if save:
            self.dump(option.workspace)

    def _on_change(self, option, dbus_notify=True):
        # we dont do anything smart, till we are started
        if not self.svc.started:
            return
        if option.callback:
            option.callback(option)

        self.notify_dbus(option)

        self._emit_change_notification(option)

    def _emit_change_notification(self, option):
        if isinstance(option, OptionItem):
            optionsmanager = self.svc.boss.get_service('optionsmanager')
            if hasattr(optionsmanager, 'events'):
                optionsmanager.emit('option_changed', option=option)

    def read_extra(self, filename, default):
        try:
            with open(filename) as file:
                return simplejson.load(file)
        except IOError:
            return default
        except Exception, e:
            return default

    def dump_data(self, filename, data):
        try:
            with open(filename, 'w') as out:
                simplejson.dump(data, out)
        except Exception, e:
            self.svc.log.exception(e)


    def read(self):
        data = {}
        for f in (self.workspace_path, self.global_path):
            try:
                with open(f) as file:
                    data.update(simplejson.load(file))
            except IOError:
                pass
            except Exception, e:
                self.svc.log.exception(e)
        return data

    def dump(self, workspace):
        data = dict((opt.name, opt.value) for opt in self if opt.workspace is workspace)
        if workspace:
            f = self.workspace_path
        else:
            f = self.global_path

        with open(f, 'w') as out:
            simplejson.dump(data, out, sort_keys=True, indent=2)

    def __len__(self):
        return len(self._options)

    def __iter__(self):
        """
        iterate the optionsitems
        """
        return self._options.itervalues()

    def __nonzero__(self):
        """
        shows if there are actually options defined for this config
        """
        return bool(self._options)

