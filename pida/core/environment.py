import os
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

def get_resource_path(resource, name):
    return environ.find_resource(resource, name)

def get_uidef_path(name):
    return get_resource_path('uidef', name)

def get_glade_path(name):
    return get_resource_path('glade', name)

def get_pixmap_path(name):
    return get_resource_path('pixmaps', name)
    


class Environment(object):

    pida_home = os.path.expanduser('~/.pida2')

    def __init__(self, argv):
        if not os.path.exists(self.pida_home):
            os.mkdir(self.pida_home)
        self.get_options(argv)
        self.env = dict(os.environ)

    def get_options(self, argv):
        op = OptionParser()
        op.add_option('-v', '--version', action='store_true',
            help=_('Print version information and exit.'))
        op.add_option('-D', '--debug', action='store_true',
            help=_('Run PIDA with added debug information.'))
        op.add_option('-T', '--trace', action='store_true',
            help=_('Run PIDA with tracing.'))
        self.opts, self.args = op.parse_args(argv)

    def is_version(self):
        return self.opts.version

    def is_debug(self):
        return self.opts.debug

    def is_trace(self):
        return self.opts.trace

    def get_base_service_directory(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'services')

    def get_local_service_directory(self):
        path = os.path.join(self.pida_home, 'services')
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def get_base_editor_directory(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'editors')

    def get_plugins_directory(self):
        path = os.path.join(self.pida_home, 'plugins')
        if not os.path.exists(path):
            os.mkdir(path)
        return path

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
