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
import urllib2

def find_files(base, service):

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
    paths.remove(service_file)
    paths.insert(1, service_file)
    print '\n'.join(paths)
    print
    return paths


def pack_plugin(base, service, notify=lambda x:None):
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



def upload_data(publisher, data, user, password,
                  notify=lambda x: None):
    authinfo = urllib2.HTTPBasicAuthHandler()
    authinfo.add_password(uri=publisher, 
                          user=user,
                          password=password,
                         )
    #XXX: proxy support 

    opener = urllib2.build_opener(authinfo)
    ret = opener.open(publisher, data=data)
    return ret.status

def upload_plugin(base, plugin, 
                  publisher,
                  user, password,
                  notify=lambda x:None):
    data = pack_plugin(base, plugin, notify=notify)

    return upload_data(publisher, data, user, password, data)


def unpack_plugin(base, content):
    io = StringIO(content)
    tarfile = TarFile.gzopen(None, content)
    tarfile.extractall(base)

