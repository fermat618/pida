
from distutils.core import setup

setup(
    name='pida',
    packages = ('pida', 'pida.core', 'pida.ui', 'pida.utils'),
    data_files = [
        #('share/gazpacho/catalogs',
        #    listfiles('gazpacho-plugin', 'pidawidgets.xml')),
        #('share/gazpacho/resources/pidawidgets',
        #    listfiles('gazpacho-plugin', 'resources', 'pidawidgets', '*.png')),
        #(get_site_packages_dir('gazpacho', 'widgets'),
        #    listfiles('gazpacho-plugin', 'pidawidgets.py')),
    ]

)
