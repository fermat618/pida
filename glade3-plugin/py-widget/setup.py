from distutils.core import setup
from os.path import join

from kiwi.dist import listfiles

glade3_prefix = '/usr/local'

setup(
    data_files=[
        (join(glade3_prefix, 'share', 'glade3', 'catalogs'),
            ('pywidgets.xml',)),
        (join(glade3_prefix, 'lib', 'glade3', 'modules'),
            ('pywidgets.py',)),
        #(join(glade3_prefix, 'share', 'glade3', 'pixmaps', '22x22'),
        #    listfiles('..', 'gazpacho-plugin', 'resources', 'kiwiwidgets', '*.png')),
        #(join(glade3_prefix, 'share', 'glade3', 'pixmaps', '16x16'),
        #    listfiles('..', 'gazpacho-plugin', 'resources', 'kiwiwidgets', '*.png')),
    ]
)
