from distutils.core import setup
from os.path import join

from kiwi.dist import listfiles

glade3_prefix = '/usr/local'

setup(
    data_files=[
        (join(glade3_prefix, 'share', 'glade3', 'catalogs'),
            ('pidawidgets.xml',)),
        (join(glade3_prefix, 'lib', 'glade3', 'modules'),
            ('pidawidgets.py',)),
    ]
)
