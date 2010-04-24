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
from pango import Font
from gtk.gdk import Color
from shutil import rmtree
import pida.utils.serialize as simplejson

import os

# locale
from pida.core.locale import Locale
locale = Locale('core')
_ = locale.gettext

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
    return [x for x in os.listdir(workspaces)
                if os.path.isdir(
                    os.path.join(workspaces, x)
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
        except Exception:
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
        return self.label.replace("_", "", 1)

    def __repr__(self):
        return '<OI %s %s:%s>' % (
                self.group.svc.get_name(),
                self.name, self.type.__name__,
                )

    no_mnemomic_label = property(_get_nlabel)

class ExtraOptionItem(object):
    """
    ExtraOptions a a little bit different from normal Options

    They can be used for example to store larger amounts of data or types
    that are not easy pickable or are very specific in form and data.
    ExtraOptions can be workspace bound and there are two options of dbus
    sharing.

    - the hole data is sent over dbus
    - no_submit is True: only a notify that the data changed is sent

    In the later case, the cached value is marked dirty and the file is read
    again from the filesystem on access.

    New ExtraOptions are generated with OptionManager.register_extra_file(...)
    """

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
        return '<ExtraOptionItem %s>' % (self.path)


manager = OptionsManager()

class OptionsConfig(BaseConfig):

    #enable reuse for keyboard shortcuts that need different name
    name = '%s.json'
    name_extra = "%s_extra_%s.json"

    def __init__(self, service, *args, **kwargs):
        BaseConfig.__init__(self, service, *args, **kwargs)


    def unload(self):
        pass #XXX: stub

    def create(self):
        self.name = self.__class__.name % self.svc.get_name()
        add_directory('workspaces', manager.workspace)
        self.workspace_path = get_settings_path('workspaces',
                                                manager.workspace, self.name)
        self.global_path = get_settings_path(self.name)
        self._options = {}
        self._extra_files = {}
        self._exports = {}
        self.create_options()
        self.register_options()


    def create_options(self):
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
                    #XXX: this writes on every change, BAD
                    self.set_value(opt.name, opt.default)

        for opt in self:
            if opt.value is None:
                self.set_value(opt.name, opt.default)


    def register_extra_option(self, name, default, callback=None,
                      safe=True, workspace=False, notify=True, path=None):
        """
        Registers an aditional option file a service uses.

        The object stored in the extra file is only one object which
        can be serialized by simplejson.

        All further accesses to the data object should happen over
        get_extra_value(name) which will make sure that other pida
        instances have syncronized data.

        The path is generated by the extra option name and the workspace flag,
        but can be overwritten trough a path argument, which must be absolute.

        """
        #XXX: support for project-level files?
        #assert not (workspace and project)
        if not path:
            path = self.__class__.name_extra % (self.svc.get_name(), name)
            if workspace:
                path = get_settings_path('workspaces', manager.workspace, path)
            else:
                path = get_settings_path(path)

        assert os.path.isabs(path)

        opt = ExtraOptionItem(self, path, default, callback, workspace,
                              notify=notify)
        self._extra_files[name] = opt

    def get_extra_value(self, name):
        """
        Returns the extra value of option 'name'
        """
        opt = self._extra_files[name]
        if opt.dirty:
            # reread the file
            opt.value = self.read_extra(opt.path, opt.default)
            opt.dirty = False

        return opt.value

    def save_extra(self, name):
        """
        Saves the extra option 'name' to the filesystem
        """
        option = self._extra_files[name]
        self.dump_data(option.path, option.value)

    def create_option(self, name, label, type, default, doc, callback=None,
                      safe=True, workspace=False):
        opt = OptionItem(self, name, label, type, default, doc,
                         callback, workspace)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def remove_option(self, option):
        """
        Removes a Option from OptionManager
        """
        del self._options[option.name]

    def get_option(self, optname):
        return self._options[optname]

    def get_extra_option(self, optname):
        return self._extra_files[optname]

    def get_value(self, name):
        return self._options[name].value

    def set_extra_value(self, name, value, dbus_notify=True, save=True):
        option = self._extra_files[name]
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

        if dbus_notify:
            pass #XXX: handle somewhere else
            #self.notify_dbus(option)

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
        except Exception:
            return default

    def dump_data(self, filename, data):
        try:
            with open(filename, 'w') as out:
                simplejson.dump(data, out)
        except Exception, e:
            self.svc.log.exception(e)


    def read(self):
        data = {}
        for f in (self.global_path, self.workspace_path):
            try:
                with open(f) as file_:
                    data.update(simplejson.load(file_))
            except ValueError, e:
                self.svc.log.error(_('Settings file corrupted: %s'), f)
            except IOError:
                pass
            except Exception, e:
                self.svc.log.exception(e)
        return data

    def dump(self, workspace):
        data = dict((opt.name, opt.value)
                    for opt in self if opt.workspace is workspace)
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

