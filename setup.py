"""
The PIDA Installer
"""

import os
import subprocess
import sys
from glob import glob

from distutils.command.build_ext import build_ext
from setuptools import setup, Extension
import pida

cmdclasses = {}
data_files = []


try:
    from sphinx.setup_command import BuildDoc
    if not os.path.exists(os.path.join("docs", "_build")):
        os.mkdir(os.path.join("docs", "_build"))
    cmdclasses["build_doc"] = BuildDoc
except ImportError:
    print "sphinx not found, skipping user docs"


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



def get_package_data():
    package_data = {
        'pida': [
            'resources/glade/*',
            'resources/pixmaps/*',
            'resources/uidef/*',
            'resources/data/*',
        ],
        'pida.utils.puilder': [
            'glade/*',
        ],
        'pida.ui': [
            'glade/*'
        ]
    }
    packages = listpackages('pida/services') + listpackages('pida/editors')
    for package in packages:
        package_data[package] = [
            'service.pida',
            'glade/*',
            'pixmaps/*',
            'uidef/*',
            'data/*',
        ]
    return package_data


cmdclasses['build_ext'] = BuildExt

data_files += [('share/doc/pida/contrib/gtkrc', glob('contrib/gtkrc/*'))]

# add docs
top = os.path.join(os.path.dirname(__file__), 'docs', '_build', 'html')
rlen = len(os.path.dirname(__file__))
for root, dirs, files in os.walk('docs/_build/html'):
    data_files += [('share/doc/pida/html%s' %root[len(top):], 
                   [os.path.join(root[rlen:], x) for x in files])]

setup(
    name = 'pida',
    version = pida.version,
    license='GPL',
    packages = listpackages('pida'),
    package_data = get_package_data(),
    ext_modules = [moo],
    cmdclass=cmdclasses,
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
    install_requires = [
        'anyvc>=0.3',
        #XXX: still needed on 2.5
        #'simplejson',
        'pygtkhelpers',
        #'vte',
        #'dbus ?',
        #'rope ?',
        #'moo ?'
        #XXX: more ?
    ],
    data_files=data_files,
)

