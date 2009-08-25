#!/usr/bin/python

from os import path
from mercurial.ui import ui as Ui
from mercurial.localrepo import localrepository as LocalRepo


ui = Ui()
repopath = path.dirname(path.dirname(path.abspath(__file__)))

repo = LocalRepo(ui, repopath)

wctx = repo['.']

plugin_files = [file for file in wctx
                if file.startswith('pida-plugins')]

bump_these = []
print 'scanning for plugins in need of a version bump'

for file in plugin_files:
    base, name = file.rsplit('/', 1)
    if name == 'service.pida': 
        #XXX: inaccurate, but reasonable
        #     will get confused about metadata changes without bump
        last_bump = wctx[file].linkrev()

        #XXX: the selection could be smarter
        last_plugin_change = max(wctx[r].linkrev()
                                 for r in plugin_files if r.startswith(base))
        needs_bump = last_bump < last_plugin_change
        if needs_bump:
            bump_these.append(
                    (path.basename(base), last_bump, last_plugin_change))

from pida.services.plugins.metadata import from_plugin, serialize

#asume relative paths
base = 'pida-plugins'
modified = repo.status()[0]
import sys
do_bump = '--bump' in sys.argv


def try_bump(version):
    """
    add 1 to the last number in the version string
    will break for non-numeric version strings
    """
    try:
        numbers = map(int, version.split('.'))
        numbers[-1]+=1
        version = '.'.join(map(str,numbers))
    except:
        pass
    return version

for name, bump, change in bump_these:
    servicefile = path.join(base, name, 'service.pida')
    # asume changes to the metadata are version bumps
    if servicefile in modified:
        continue

    metadata = from_plugin(base, name)
    new_version = try_bump(metadata.version)
    print '%15s %s -> %s' %(name, metadata.version, new_version)
    if do_bump:
        metadata.version = new_version

        serialize(base, name, metadata)

