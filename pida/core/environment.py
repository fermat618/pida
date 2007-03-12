
from kiwi.environ import Library, environ

library = Library('pida', root='../..')

library.add_global_resource('glade', 'glade')
library.add_global_resource('uidef', 'uidef')

def get_resource_path(resource, name):
    return environ.find_resource(resource, name)

def get_uidef_path(name):
    return get_resource_path('uidef', name)
