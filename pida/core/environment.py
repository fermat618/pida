import os
import sys
from optparse import OptionParser

from kiwi.environ import Library, environ

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

library = Library('pida', root='../')

library.add_global_resource('glade', 'resources/glade')
library.add_global_resource('uidef', 'resources/uidef')
library.add_global_resource('pixmaps', 'resources/pixmaps')
library.add_global_resource('data', 'resources/data')

def get_resource_path(resource, name):
    return environ.find_resource(resource, name)

def get_uidef_path(name):
    return get_resource_path('uidef', name)

def get_glade_path(name):
    return get_resource_path('glade', name)

def get_pixmap_path(name):
    return get_resource_path('pixmaps', name)

def get_data_path(name):
    return get_resource_path('data', name)

pida_home = os.path.expanduser('~/.pida2')
firstrun_filename = os.path.join(pida_home, 'first_run_wizard')
plugins_dir = os.path.join(pida_home, 'plugins')

if not os.path.exists(pida_home):
    os.mkdir(pida_home)

op = OptionParser()
op.add_option('-v', '--version', action='store_true',
    help=_('Print version information and exit.'))
op.add_option('-D', '--debug', action='store_true',
    help=_('Run PIDA with added debug information.'))
op.add_option('-T', '--trace', action='store_true',
    help=_('Run PIDA with tracing.'))
op.add_option('-F', '--firstrun', action='store_true',
    help=_('Run the PIDA first run wizard.'))

opts, args = op.parse_args(sys.argv)
env = dict(os.environ)

def is_version():
    return opts.version

def is_debug():
    return opts.debug

def is_trace():
    return opts.trace

def is_firstrun():
    return opts.firstrun

def has_firstrun():
    return os.path.exists(firstrun_filename)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
