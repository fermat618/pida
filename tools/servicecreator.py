
from optparse import OptionParser
import sys, os
from datetime import date

def log(txt):
    print txt

python_module_template = '''# -*- coding: utf-8 -*- 

# Copyright (c) %(year)s The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# System import(s)

# GTK import(s)

# Library import(s)

# PIDA import(s)
%(content)s

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
'''

plugin_template = '''from pida.core.service import Service

# Service class
class %(name)s(Service):
    """Describe your Service Here""" 

# Required Service attribute for service loading
Service = %(name)s

'''

def create_plugin_dir(root_path, name):
    if not os.path.isdir(root_path):
        raise ValueError('The root path is not a directory')
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
    content = plugin_template % dict(name=modname.capitalize())
    data = python_module_template % dict(
        content=content,
        year = date.today().year
    )
    f.write(data)
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
    os.system('svn add %s' % path)

def create_module(root_path, name):
    if not name.endswith('.py'):
        name = '%s.py' % name
    path = os.path.join(root_path, name)
    data = python_module_template % dict(
            content='',
            year=date.today().year
    )
    log('Creating module %s at %s' % (name, path))
    f = open(path, 'w')
    f.write(data)
    f.close()
    testname = 'test_%s' % name
    log('Creating test module %s at %s' % (testname, path))
    test_path = os.path.join(root_path, testname)
    f = open(test_path, 'w')
    f.write(data)
    f.close()
    os.system('svn add %s %s' % (path, test_path))

def get_service_details():
    defpath = os.path.join(os.getcwd(), 'pida', 'services')
    path = raw_input('Please enter the path for the service [%s]: ' % defpath)
    if not path:
        path = defpath
    name = ''
    while not name:
        name = raw_input('Please enter the Service name: ')
    return path, name.lower()

def get_module_details():
    defpath = os.getcwd()
    path = raw_input('Please enter the path for the module [%s]: ' % defpath)
    if not path:
        path = defpath
    name = ''
    while not name:
        name = raw_input('Please enter the module name: ')
    return path, name.lower()

def main(argv):
    if len(argv):
        act = argv[0]
    else:
        act = 'module'
    if act == 'module':
        path, name = get_module_details()
        create_module(path, name)
    elif act == 'service':
        path, name = get_service_details()
        create_plugin(path, name)





if __name__ == '__main__':
    main(sys.argv[1:])
