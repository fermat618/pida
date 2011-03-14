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
from argparse import ArgumentParser
from functools import partial

import py

import gtk
import pida
# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


base_path = py.path.local(pida.__file__).pypkgpath()

resources = dict(uidef=[], pixmaps=[], data=[])

def find_resource(kind, name):
    for item in resources[kind]:
        full = item/name
        if full.check():
            return str(full)
    raise EnvironmentError('Could not find %s resource: %s' % (kind, name))

def add_global_base(service_path):
    service_path = py.path.local(service_path)
    for kind in 'uidef', 'pixmaps', 'data':
        path = service_path/kind
        if path.check(dir=True):
            resources[kind].append(path)

add_global_base(base_path/'resources')

get_pixmap_path = partial(find_resource, 'pixmaps')
get_data_path = partial(find_resource, 'data')


def home():
    return py.path.local(os.path.expanduser(opts.pida_home))

def firstrun_file():
    return home()/'first_run_wizard'

def settings_dir():
    return home()/'settings'

def plugins_dir():
    return home().ensure('plugins', dir=1)
plugins_path = []
def setup_plugins_paths():
    #XXX: development hack
    buildin_plugins_dir = base_path.dirpath()/'pida-plugins'

    if buildin_plugins_dir.check(dir=1):
        plugins_path[:] = [str(plugins_dir()), str(buildin_plugins_dir)]
    else:
        plugins_path[:] = [str(plugins_dir())]

def parse_gtk_rcfiles():
    gtk.rc_add_default_file(get_data_path('gtkrc-2.0'))
    gtk.rc_add_default_file(str(home()/"gtkrc-2.0"))
    # we have to force reload the settings
    gtk.rc_reparse_all_for_settings(gtk.settings_get_default(), True)



parser = ArgumentParser()
parser.add_argument(
    '-v', '--version', action='store_true',
    help=_('Print version information and exit.'))
parser.add_argument(
    '-D', '--debug', action='store_true',
    help=_('Run PIDA with added debug information.'))
parser.add_argument(
    '-T', '--trace', action='store_true',
    help=_('Run PIDA with tracing.'))
parser.add_argument(
    '-F', '--firstrun', action='store_true',
    help=_('Run the PIDA first run wizard.'))
parser.add_argument(
    '--safe_mode', action='store_true',
    help=_('Starts PIDA in safe mode. Useful when PIDA doesn\'t start anymore'))
parser.add_argument(
    '-P', '--profile', dest="profile_path",
    help=_('Generate profile data on path.'))
parser.add_argument(
    '-w', '--workspace', dest="workspace",
    help=_('Use workspace name'))
parser.add_argument(
    '-m', '--manager', action='store_true',
    help=_('Show workspace Manager'))
parser.add_argument(
    '--killsettings', action="store_true",
    help=_('Resets all settings of pida to their default'))
parser.add_argument('--pida-home', default='~/.pida2')
parser.add_argument('files', nargs='*', default=[])


env = dict(os.environ)

on_windows = sys.platform == 'win32' #XXX: checked only on xp
opts = None

def parse_args(argv):
    global opts
    opts = parser.parse_args(argv)

    if opts.killsettings:
        opts.firstrun = True

    setup_plugins_paths()
    parse_gtk_rcfiles()
    return opts


parse_args([])


def is_debug():
    return opts.debug

def is_firstrun():
    return not firstrun_file().check() or opts.firstrun

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

def get_plugin_global_settings_path(name, filename=None):
    path = home().ensure(name, dir=1)
    if filename is not None:
        return str(path/filename)
    return str(path)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
