# -*- coding: utf-8 -*-
"""
    Environment
    ~~~~~~~~~~~

    This module provides some basic environment informations

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import sys
from optparse import OptionParser
from functools import partial

import pida
# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


base_path = os.path.dirname(pida.__file__)

class FakeLibrary(dict):
    def find_resource(self, resource, name):
        for item in self[resource]:
            full = os.path.join(item, name)
            if os.path.exists(full):
                return full
        raise EnvironmentError('Could not find %s resource: %s' % (
                                resource, name))

    def add_global_base(self, service_path):
        for kind in 'glade', 'uidef', 'pixmaps', 'data':
            path = os.path.join(service_path, kind)
            if os.path.isdir(path):
                self[kind].append(path)

library = FakeLibrary(glade=[], uidef=[], pixmaps=[], data=[])
library.add_global_base(os.path.join(base_path, 'resources'))

get_resource_path = library.find_resource
get_pixmap_path = partial(get_resource_path, 'pixmaps')
get_data_path = partial(get_resource_path, 'data')

pida_home = os.path.expanduser('~/.pida2')
firstrun_filename = os.path.join(pida_home, 'first_run_wizard')
plugins_dir = os.path.join(pida_home, 'plugins')
settings_dir = os.path.join(pida_home, 'settings')

pida_root_path = os.path.dirname(os.path.abspath(pida.__path__[0]))

for path in pida_home, plugins_dir:
    if not os.path.exists(path):
        os.mkdir(path)

import gtk

gtk.rc_add_default_file(get_data_path('gtkrc-2.0'))
gtk.rc_add_default_file(os.path.join(pida_home, "gtkrc-2.0"))
# we have to force reload the settings
gtk.rc_reparse_all_for_settings(gtk.settings_get_default(), True)

#XXX: development hack
buildin_plugins_dir = os.path.join(base_path, 'pida-plugins')

if os.path.exists(buildin_plugins_dir):
    plugins_path = [plugins_dir, buildin_plugins_dir]
else:
    plugins_path = [plugins_dir]


op = OptionParser()
op.add_option('-v', '--version', action='store_true',
    help=_('Print version information and exit.'))
op.add_option('-D', '--debug', action='store_true',
    help=_('Run PIDA with added debug information.'))
op.add_option('-T', '--trace', action='store_true',
    help=_('Run PIDA with tracing.'))
op.add_option('-F', '--firstrun', action='store_true',
    help=_('Run the PIDA first run wizard.'))
op.add_option('--safe_mode', action='store_true',
    help=_('Starts PIDA in safe mode. Usefull when PIDA doesn\'t start anymore'))
op.add_option('-P', '--profile', dest="profile_path",
    help=_('Generate profile data on path.'))
op.add_option('-w', '--workspace', dest="workspace",
    help=_('Use workspace name'))
op.add_option('-m', '--manager', action='store_true',
    help=_('Show workspace Manager'))
op.add_option('', '--killsettings', action="store_true",
    help=_('Resets all settings of pida to their default'))

opts, args = op.parse_args([])

env = dict(os.environ)

on_windows = sys.platform == 'win32' #XXX: checked only on xp

def parse_args(argv):
    global opts, args
    opts, args = op.parse_args(argv)

    if opts.killsettings:
        opts.firstrun = True


def is_debug():
    return opts.debug

def is_firstrun():
    return not os.path.exists(firstrun_filename) or opts.firstrun

def is_safe_mode():
    return opts.safe_mode

def workspace_name():
    if not opts.workspace:
        return "default"
    return opts.workspace

def workspace_set():
    return opts.workspace is not None

def workspace_manager():
    return opts.manager

def killsettings():
    return opts.killsettings

def get_args():
    return args

def get_plugin_global_settings_path(name, filename=None):
    path = os.path.join(pida_home, name)
    if not os.path.exists(path):
        os.makedirs(path)
    if filename is not None:
        return os.path.join(path, filename)
    return path

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
