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

for file in plugin_files:
    # we only want plugins
    base, name = file.rsplit('/', 1)
    if name == 'service.pida': 
        #XXX: inaccurate, but reasonable
        last_bump = wctx[file].linkrev()

        #XXX: the selection could be smarter
        last_plugin_change = max(wctx[r].linkrev()
                                 for r in plugin_files if r.startswith(base))
        needs_bump = last_bump < last_plugin_change

        print path.basename(base), \
              last_bump, last_plugin_change, \
              'bump' if needs_bump else 'ignore'
