from distutils.core import setup

from kiwi.dist import listfiles

setup(
    data_files=[
        ('/usr/local/share/glade3/catalogs', ('kiwiwidgets.xml',)),
        ('/usr/local/lib/glade3/modules', ('kiwiwidgets.py',)),
        ('/usr/local/share/glade3/pixmaps/22x22',
            listfiles('..', 'gazpacho-plugin', 'resources', 'kiwiwidgets', '*.png')),
        ('/usr/local/share/glade3/pixmaps/16x16',
            listfiles('..', 'gazpacho-plugin', 'resources', 'kiwiwidgets', '*.png')),
    ]
)
