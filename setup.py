

import os
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext
from tools.moo.dsutils import pkc_get_include_dirs, pkc_get_libraries, pkc_get_library_dirs
  
moo = Extension('moo_stub', 
                 ['moo/moopaned.c',
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
            if os.system('cd tools/moo && make prepare'):
                raise RuntimeError()
        build_ext.build_extension(self, ext)
  
setup(
      name='pida',
      packages = ('pida',),
      ext_modules = [moo],
      data_files = [],
          #('share/gazpacho/catalogs',
          #    listfiles('gazpacho-plugin', 'pidawidgets.xml')),
      cmdclass={'build_ext': BuildExt},
)
