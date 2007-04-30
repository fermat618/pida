"""
The PIDA Installer
"""

import os
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

from pida import PIDA_VERSION


# Moo Extension
from moo.dsutils import pkc_get_include_dirs, pkc_get_libraries, pkc_get_library_dirs
moo = Extension(
    'moo_stub', 
    [
        'moo/moopaned.c',
        'moo/moobigpaned.c',
        'moo/moomarshals.c',
        'moo/moo-pygtk.c',
        'moo/moo-stub.c',
    ],
    include_dirs=pkc_get_include_dirs('gtk+-2.0 pygtk-2.0'),
    libraries=pkc_get_libraries('gtk+-2.0 pygtk-2.0'),
    library_dirs=pkc_get_library_dirs('gtk+-2.0 pygtk-2.0'),
)


class BuildExt(build_ext):
    def build_extension(self, ext):
        if ext.name == 'moo_stub':
            if os.system('cd moo && make prepare'):
                raise RuntimeError()
        build_ext.build_extension(self, ext)


# Modified from kiwi
def listpackages(root):
    packages = []
    if os.path.exists(os.path.join(root, '__init__.py')):
        packages.append(root.replace('/', '.'))
    for filename in os.listdir(root):
        full = os.path.join(root, filename)
        if os.path.isdir(full):
            packages.extend(listpackages(full))
    return packages


def list_pida_packages():
    packages = []
    for package in ['pida', 'pida/core', 'pida/ui', 'pida/utils']:
        packages.extend(listpackages(package))
    return packages


def list_pida_services(package_data):
    packages = listpackages('pida/services') + listpackages('pida/editors')
    for package in packages:
        package_data[package] = [
            'service.pida',
            'glade/*',
            'pixmaps/*',
            'uidef/*',
            'data/*'
        ]
    return packages


def get_main_data():
    return {
        'pida':
        [
            'resources/glade/*',
            'resources/pixmaps/*',
            'resources/uidef/*'
        ]
    }

all_package_data = get_main_data()

all_packages = list_pida_packages() + list_pida_services(all_package_data)

setup(
    name='pida',
    version = PIDA_VERSION,
    packages = all_packages,
    package_data = all_package_data,
    ext_modules = [moo],
    cmdclass={'build_ext': BuildExt},
    scripts=['bin/pida', 'bin/pida-remote'],
    author = 'Ali Afshar',
    author_email = 'aafshar@gmail.com',
    url = 'http://pida.co.uk/',
    download_url = 'http://pida.co.uk/download/',
    description = 'An intergated development environment that reuses tools such as Vim, and all version control systems.',
)

