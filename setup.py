

from kiwi.dist import setup, listfiles, listpackages, get_site_packages_dir

setup(
    name='pida',
    packages = listpackages('pida'),
    data_files = [
        #('share/gazpacho/catalogs',
        #    listfiles('gazpacho-plugin', 'pidawidgets.xml')),
        #('share/gazpacho/resources/pidawidgets',
        #    listfiles('gazpacho-plugin', 'resources', 'pidawidgets', '*.png')),
        #(get_site_packages_dir('gazpacho', 'widgets'),
        #    listfiles('gazpacho-plugin', 'pidawidgets.py')),
    ]

)
