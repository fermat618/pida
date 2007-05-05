
from optparse import OptionParser
import sys, os
from datetime import date

def log(txt):
    print txt

python_module_template = '''# -*- coding: utf-8 -*- 

# Copyright (c) %(year)s %(copyright_holder)s

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

%(system_imports)s
%(gtk_imports)s
%(library_imports)s
%(pida_imports)s

%(content)s

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
'''


def create_python_file(root_path, name, content,
                       copyright_holder='The PIDA Project',
                       s_imports=[],
                       g_imports=[],
                       l_imports=[],
                       p_imports=[]):
    if not name.endswith('.py'):
        name = '%s.py' % name

    path = os.path.join(root_path, name)
    f = open(path, 'w')

    if s_imports:
        s_imports.insert(0, '# Standard Library Imports')
    sys_imports = '\n'.join(s_imports)

    if g_imports:
        g_imports.insert(0, '# GTK Imports')
    gtk_imports = '\n'.join(g_imports)

    if l_imports:
        l_imports.insert(0, '# Other Imports')
    library_imports = '\n'.join(l_imports)

    if p_imports:
        p_imports.insert(0, '# PIDA Imports')
    pida_imports = '\n'.join(p_imports)

    data = python_module_template % dict(
            content=content,
            copyright_holder=copyright_holder,
            system_imports=sys_imports,
            gtk_imports=gtk_imports,
            library_imports=library_imports,
            pida_imports=pida_imports,
            year=date.today().year,
    )

    f.write(data)
    f.close()


class ServiceCreator(object):

    service_template = '''
# locale
from pida.core.locale import Locale
locale = Locale('%(lowername)s')
_ = locale.gettext

# Service class
class %(name)s(Service):
    """Describe your Service Here""" 

# Required Service attribute for service loading
Service = %(name)s

'''

    service_template_imports = dict(
        p_imports = [
            'from pida.core.service import Service',
            'from pida.core.features import FeaturesConfig',
            'from pida.core.commands import CommandsConfig',
            'from pida.core.events import EventsConfig',
            'from pida.core.actions import ActionsConfig',
            'from pida.core.options import OptionsConfig',
            'from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE',
        ]
    )
    
    def __init__(self, root_path, name, opts):
        self._name = name
        self._root_path = root_path
        self._path = os.path.abspath(os.path.join(self._root_path, self._name))
        self._opts = opts

    def _create_service_text(self):
        return self.service_template % dict(name=self._name.capitalize(),
                                            lowername=self._name)

    def _create_service_dir(self):
        if not os.path.isdir(self._root_path):
            raise ValueError('The root path is not a directory')
        if os.path.exists(self._path):
            raise ValueError('The plugin directory already exists')
        else:
            os.mkdir(self._path)

    def _create_service_module(self):
        contents = self._create_service_text()
        create_python_file(self._path, self._name, contents, **self.service_template_imports)
        create_python_file(self._path, '__init__', '')
        create_python_file(self._path, 'test_%s' % self._name, '')

    def _create_servicefile(self):
        servicefile_path = os.path.join(self._path, 'service.pida')
        f = open(servicefile_path, 'w')
        f.close()

    def _create_resource_dirs(self):
        for res in ['glade', 'data', 'uidef', 'pixmaps', 'locale']:
            respath = os.path.join(self._path, res)
            os.mkdir(respath)

    def _add_svn(self):
        if self._opts.add_svn:
            os.system('svn add %s' % self._path)


    def create(self):
        log('Creating service %s in %s' % (self._name, self._root_path))
        self._create_service_dir()
        self._create_service_module()
        self._create_servicefile()
        self._create_resource_dirs()
        self._add_svn()


class ModuleCreator(object):
    
    def __init__(self, root_path, name, opts):
        self._name = name
        self._root_path = root_path
        self._path = os.path.join(self._root_path, name)
        self._opts = opts

    def _create_module(self):
        create_python_file(self._root_path, self._name, '')

    def _create_test_module(self):
        create_python_file(self._root_path,
            'test_%s' % self._name,
            '',
            s_imports=[
                'from unittest import TestCase'
            ]
        )

    def create(self):
        self._create_module()
        self._create_test_module()
        self._add_svn()

    def _add_svn(self):
        if self._opts.add_svn:
            os.system('svn add %s' % self._path)


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


def prime_parser():
    usage = "usage: %prog [options] module|m|service|s"
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--no-svn',
        help='Do not add the creation to the subversion repo',
        dest='add_svn',
        action='store_false',
        default=True)
    return parser

def main():
    parser = prime_parser()
    opts, args = parser.parse_args()
    if not args:
        parser.error('You must provide an action')
    act = args[0]
    if act in ['module', 'm']:
        path, name = get_module_details()
        ModuleCreator(path, name, opts).create()
    elif act in ['service', 's']:
        path, name = get_service_details()
        ServiceCreator(path, name, opts).create()
    else:
        parser.error('The action must be one of "module" or "m" for a module,'
                     ' or "service" or "s" for a service')


if __name__ == '__main__':
    main()
