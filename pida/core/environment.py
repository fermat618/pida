import os

from kiwi.environ import Library, environ

library = Library('pida', root='../..')

library.add_global_resource('glade', 'resources/glade')
library.add_global_resource('uidef', 'resources/uidef')

def get_resource_path(resource, name):
    return environ.find_resource(resource, name)

def get_uidef_path(name):
    return get_resource_path('uidef', name)

def get_glade_path(name):
    return get_resource_path('glade', name)


class Environment(object):

    def get_base_service_directory(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'services')
