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
from shutil import rmtree
import simplejson


from os import path
import os
get_settings_path = partial(os.path.join, settings_dir)

def add_directory(*parts):
    dir = get_settings_path(*parts)
    if not os.path.exists(dir):
        os.makedirs(dir)

def unset_directory(*parts):
    #XXX: reload=!
    rmtree(get_settings_path(*parts))

def initialize():
    add_directory('keyboard_shortcuts')
    add_directory('workspaces')

def list_sessions(self):
    """Returns a list with all session names """
    workspaces = get_settings_path('workspaces')
    return [ x for x in os.listdir(workspaces)
                if path.isdir(
                    path.join(workspaces, x)
                )
            ]

class OptionsManager(object):

    def __init__(self, session=None):

        initialize()
        self._session = None
        if session:
            self.session = session
        if killsettings():
            unset_directory()

    def initialize_session(self):
        add_directory('workspaces', self.session)

    def open_session_manager(self):
        pass #XXX: get this from the options somehow

    def _set_session(self, value):
        self._session = value
        self.initialize_session()

    def _get_session(self):
        if self._session is None:
            # we need this form of lazy loading because the default manager
            # is created so early that the session name is not known then
            import pida.core.environment
            self._session = pida.core.environment.session_name()
        return self._session

    session = property(_get_session, _set_session)

    def on_change(self, option):
        pass #XXX: implement


def choices(choices):
    """Helper to generate string options for choices"""
    class Choices(str):
        """Option that should be one of the choices"""
        options = choices
    return Choices

class Color(str): """Option which is a color in RGB Hex"""


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc, callback, 
                 session=None):
        self.group = group
        self.name = name
        self.label = label
        self.type = rtype
        self.doc = doc
        self.default = default
        self.session = bool(session)
        self.callback = callback
        self.value = None

    def add_notify(self, callback, *args):
        import warnings
        warnings.warn("deprecated", DeprecationWarning)

manager = OptionsManager()

class OptionsConfig(BaseConfig): 

    #enable reuse for keyboard shortcuts that need different name
    name='%s.json'

    def create(self):
        self.name = self.__class__.name%self.svc.get_name()
        self.workspace_path = get_settings_path('workspaces', manager.session, self.name)
        self.global_path = get_settings_path(self.name)
        self._options = {}
        self.create_options()
        self.register_options()


    def create_options(self) :
        """Create the options here"""

    def register_options(self):
        # in safemode we reset all dangerouse variables so pida can start
        # even if there are some settings + pida bugs that cause problems
        # default values MUST be safe
        self.svc.log.debug(self._options.keys())
        for name, value in self.read().items():
            self.svc.log("%s %r", name, value)

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

    def create_option(self, name, label, type, default, doc, callback=None, 
                      safe=True, session=False):
        opt = OptionItem(self, name, label, type, default, doc,
                         callback, session)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]

    def get_value(self, name):
        return self._options[name].value

    def set_value(self, name, value):
        option = self._options[name]
        option.value = value
        self._on_change(option)
        self.dump(option.session)

    def _on_change(self, option):
        if option.callback:
            option.callback(option)
        self.svc.boss.get_service('optionsmanager').emit('option_changed', option=option)

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

    def dump(self, session):
        data = dict((opt.name, opt.value) for opt in self if opt.session is session)
        if session:
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

