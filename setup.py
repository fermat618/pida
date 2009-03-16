"""
The PIDA Installer
"""

import os
import subprocess
import sys

from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

import pida

# Check availability of pygtk 2.0
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
            subprocess.check_call(['make', 'prepare'],
                cwd=os.path.join(os.path.dirname(__file__),'contrib/moo')
            )
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
    name = 'pida',
    version = pida.version,
    packages = all_packages,
    package_data = all_package_data,
    ext_modules = [moo],
    cmdclass={'build_ext': BuildExt},
    scripts=['bin/pida', 'bin/pida-remote', 'bin/pida-build', 'bin/pida-pyshell'],
    author = pida.author,
    author_email = pida.author,
    url = pida.website,
    download_url = pida.website + 'download/',
    description = pida.short_description,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Topic :: Software Development',
        'Topic :: Software Development :: Version Control',
        'Topic :: Text Editors',
        'Topic :: Utilities',
    ],
    requires = [
        #XXX: more ?
        'anyvc (>= 0.2)',
        'simplejson',
        'PyGtk (>= 2.14)',
        #'kiwi-gtk (>= 1.9.23)', #XXX distutils doesnt like the -
        #'vte',
        #'dbus ?',
        #'rope ?',
        #'moo ?'
    ]
)

