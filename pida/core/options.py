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
from pida.utils import json

import py

from pango import Font
from gtk.gdk import Color

from .base import BaseConfig
from .environment import is_safe_mode, killsettings, settings_dir, workspace_name
# locale
from pida.core.locale import Locale
locale = Locale('core')
_ = locale.gettext

def add_directory(*parts):
    return settings_dir().ensure(*parts, dir=True)

def unset_directory(*parts):
    #XXX: reload=!
    path = settings_dir().join(*parts)
    if path.check():
        path.remove()

def initialize():
    add_directory('workspaces')

def list_workspaces():
    """Returns a list with all workspace names """
    workspaces = settings_dir().join('workspaces')
    return [x.basename for x in workspaces.listdir() if x.check(dir=True)]


def must_open_workspace_manager():
    data = json.load(settings_dir()/'appcontroller.json', fallback={})
    return bool(data.get('open_workspace_manager', False))


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


    def _set_workspace(self, value):
        self._workspace = value
        self.initialize_workspace()

    def _get_workspace(self):
        if self._workspace is None:
            # we need this form of lazy loading because the default manager
            # is created so early that the workspace name is not known then
            self._workspace = workspace_name()
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
        self.group.set_value(self.name, value)

    def _get_nlabel(self):
        return self.label.replace("_", "", 1)

    def __repr__(self):
        return '<OI %s %s:%s>' % (
                self.group.svc.get_name(),
                self.name, self.type.__name__,
                )

    no_mnemomic_label = property(_get_nlabel)


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
        self.workspace_path = settings_dir().join('workspaces',
                                                manager.workspace, self.name)
        self.global_path = settings_dir().join(self.name)
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

    def read_extra(self, path, default):
        try:
            return json.load(path)
        except: #XXX: handle corrupt files better
            return default

    def dump_data(self, path, data):
        try:
            json.dump(data, path)
        except Exception, e:
            self.svc.log.exception(e)


    def read(self):
        data = {}
        for f in (self.global_path, self.workspace_path):
            try:
                data.update(json.load(f))
            except ValueError, e:
                self.svc.log.error(_('Settings file corrupted: {file}'), file=f)
            except py.error.ENOENT:
                pass
            except Exception, e:
                self.svc.log.exception(e)
        return data

    def dump(self, workspace):
        data = dict((opt.name, opt.value)
                    for opt in self if opt.workspace is workspace)
        if workspace:
            path = self.workspace_path
        else:
            path = self.global_path

        json.dump(data, path)

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

