"""
The PIDA Installer
"""
from pida.utils import hgdistver

import os
import subprocess
import sys
from glob import glob

from distutils.command.build_ext import build_ext
from setuptools import setup, find_packages, Extension
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
from commands import getoutput

def pkc_get_dirs(option, *names):
    output = getoutput(' '.join(['pkg-config', option] + list(names)))
    return output.replace(option[-2:], '').split()

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
    include_dirs=pkc_get_dirs('--cflags-only-I', 'gtk+-2.0', 'pygtk-2.0'),
    libraries=pkc_get_dirs('--libs-only-l', 'gtk+-2.0', 'pygtk-2.0'),
    library_dirs=pkc_get_dirs('--libs-only-L', 'gtk+-2.0', 'pygtk-2.0'),
)


class BuildExt(build_ext):
    def build_extension(self, ext):
        if ext.name == 'pida.ui.moo_stub':
            subprocess.check_call(['make', 'prepare'],
                cwd=os.path.join(os.path.dirname(__file__),'contrib/moo')
            )
        build_ext.build_extension(self, ext)




install_requires = [
    'anyvc>=0.3.2',
    'py>=1.3',
    'bpython>=0.9.7',
    'pygtkhelpers>0.4.2',
    'flatland',
    'logbook',
    #'vte',
    #'dbus ?',
    #'rope ?',
    #'moo ?'
    #XXX: more ?
]

if sys.version_info < (2, 7):
    install_requires.append('argparse')

setup(
    name = 'pida',
    version = hgdistver.get_version(),
    license='GPL',
    packages = find_packages(exclude=['tests', 'tests.*']),
    ext_modules = [moo],
    cmdclass={'build_ext': BuildExt},
    scripts = [
        'bin/pida',
        'bin/pida-remote',
        'bin/pida-build',
    ],
    author = pida.author,
    author_email = pida.author,
    url = pida.website,
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
        'Topic :: Text Editors :: Integrated Development Environments (IDE)',
        'Topic :: Text Editors :: Emacs',
        'Topic :: Utilities',
        'Programming Language :: Python'
    ],
    data_files=[('share/doc/pida/contrib/gtkrc', glob('contrib/gtkrc/*'))],
    install_requires=install_requires,
    package_data = {
        'pida': [
            'resources/glade/*',
            'resources/pixmaps/*',
            'resources/uidef/*',
            'resources/data/*',
        ],
        '': [
            'glade/*',
            'pixmaps/*',
            'uidef/*',
            'data/*',
        ]
    },
)

