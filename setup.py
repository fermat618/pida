"""
The PIDA Installer
"""

import os
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

from pida import PIDA_VERSION, PIDA_AUTHOR, PIDA_WEBSITE, \
                 PIDA_SHORT_DESCRIPTION, PIDA_NAME

# Check availability of pygtk 2.0
import subprocess, sys
NO_PYGTK_ERROR_MESSAGE = """pkg-config reports your system misses pygtk 2.0.
PIDA needs pygtk headers at compile time. These can generally be found in the
python-dev or python-gtk2-dev package of your distribution.
"""
if subprocess.call(['pkg-config', '--exists', 'pygtk-2.0']) != 0:
    print NO_PYGTK_ERROR_MESSAGE
    sys.exit(1)


# Moo Extension
from dsutils import pkc_get_include_dirs, pkc_get_libraries, pkc_get_library_dirs
moo = Extension(
    'pida.ui.moo_stub', 
    [ 'contrib/moo/%s'%c for c in [
        'moopane.c',
        'moopaned.c',
        'moobigpaned.c',
        'marshals.c',
        'moo-pygtk.c',
        'moo-stub.c',
        'moopython-utils.c',
    ]],
    include_dirs=pkc_get_include_dirs('gtk+-2.0', 'pygtk-2.0'),
    libraries=pkc_get_libraries('gtk+-2.0', 'pygtk-2.0'),
    library_dirs=pkc_get_library_dirs('gtk+-2.0', 'pygtk-2.0'),
)


class BuildExt(build_ext):
    def build_extension(self, ext):
        if ext.name == 'pida.ui.moo_stub':
            if os.system('cd contrib/moo && make prepare'):
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
            'data/*',
            'locale/fr_FR/LC_MESSAGES/*',
        ]
    return packages


def get_main_data():
    return {
        'pida':
        [
            'resources/glade/*',
            'resources/pixmaps/*',
            'resources/uidef/*',
            'resources/data/*',
            'resources/locale/fr_FR/LC_MESSAGES/*',
            'utils/puilder/glade/*',
        ]
    }

all_package_data = get_main_data()

all_packages = list_pida_packages() + list_pida_services(all_package_data)

setup(
    name = PIDA_NAME,
    version = PIDA_VERSION,
    packages = all_packages,
    package_data = all_package_data,
    ext_modules = [moo],
    cmdclass={'build_ext': BuildExt},
    scripts=['bin/pida', 'bin/pida-remote', 'bin/pida-build', 'bin/pida-pyshell'],
    author = PIDA_AUTHOR,
    author_email = PIDA_AUTHOR,
    url = PIDA_WEBSITE,
    download_url = PIDA_WEBSITE + 'download/',
    description = PIDA_SHORT_DESCRIPTION,
)

