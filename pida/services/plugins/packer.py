"""
    Pida Plugin Packer
    ~~~~~~~~~~~~~~~~~~

    :license: GPL2 or later
    :copright: 2009 by the pida team
"""

import os
from os import path
from tarfile import TarFile
from StringIO import StringIO

def find_files(base, service):
    base = path.normpath(base)
    service_file = path.join(service, 'service.pida')
    service_path = path.join(base, service)
    # find a better way
    nasty_dirs = '.svn', 'CVS', '.git', '.hg', '.bzr'
    nasty_ext = 'pyc', 'o', 'class'
    paths = [service_path]
    for top, dirs, files in os.walk(service_path):
        dirs[:] = [d for d in dirs if d not in nasty_dirs]
        files = [ x
                 for x in files 
                 if not any(
                     x.endswith(e)
                     for e in nasty_ext
                 )
                ]
        all = dirs + files
        paths.extend(path.join(top, x) for x in all)

    # sort out some duplicates
    paths = sorted(set(x[len(base)+1:] for x in paths))
    # per convention the service file is the second item
    if service_file in paths:
        paths.remove(service_file)
    paths.insert(1, service_file)
    return paths

def _default_notify(text):
    print text

def pack_plugin(base, service, notify=_default_notify):
    service_file = path.join(base, service, 'service.pida')
    base_len = len(base)
    if not path.exists(service_file):
        return
    notify('Finding Files ...')
    paths = find_files(base, service)
    notify('Building  Tarball ...')

    tar_io = StringIO()
    tarfile = TarFile.open(mode='w:gz', fileobj=tar_io)
    for name in paths:
        tarfile.add(
            path.normpath(path.join(base, name)),
            arcname=name,
            recursive=False,
        )
    tarfile.close()
    return tar_io.getvalue()




