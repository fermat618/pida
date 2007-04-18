import os

from kiwi.environ import Library, environ

library = Library('pida', root='../..')

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

    def __init__(self):
        if not os.path.exists(self.pida_home):
            os.mkdir(self.pida_home)

    def get_base_service_directory(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'services')

    def get_base_editor_directory(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'editors')

