
from optparse import OptionParser
import sys, os

def log(txt):
    print txt

plugin_template = '''
# pida imports
from pida.core.service import Service

# Service class
class %(name)s(Service):
    """Describe your Service Here""" 

Service = %(name)s

'''

def create_plugin_dir(root_path, name):
    path = os.path.abspath(os.path.join(root_path, name))
    if os.path.exists(path):
        raise ValueError('The plugin directory already exists')
    else:
        os.mkdir(path)
        return path

def create_plugin_module(path, name):
    modname = '%s.py' % name
    modpath = os.path.join(path, modname)
    f = open(modpath, 'w')
    f.write(plugin_template % dict(name=modname.capitalize()))
    f.close()
    initpath = os.path.join(path, '__init__.py')
    f = open(initpath, 'w')
    f.close()

def create_servicefile(path):
    servicefile_path = os.path.join(path, 'service.pida')
    f = open(servicefile_path, 'w')
    f.close()

def create_resource_dirs(path):
    for res in ['glade', 'data', 'uidef', 'pixmaps']:
        respath = os.path.join(path, res)
        os.mkdir(respath)

def create_plugin(root_path, name):
    log('Making plugin directory in %s' % root_path)
    path = create_plugin_dir(root_path, name)
    log('Creating plugin module named %s at %s' % (path, name))
    create_plugin_module(path, name)
    log('Creating service.pida in %s' % path)
    create_servicefile(path)
    log('Creating Resource directories in %s' % path)
    create_resource_dirs(path)

def main():
    create_plugin('/tmp', 'mytestplugin')




if __name__ == '__main__':
    main()
