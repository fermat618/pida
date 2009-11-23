
from os.path import join, dirname
import os
from shutil import copy

found = False

for path in os.environ['PATH'].split(os.pathsep):
    path = join(path, 'glade-3')
    if os.access(path, os.X_OK):
        found = True
        break

if not found:
    print "glade-3 not found in path"
    raise SystemExit

glade3_prefix = dirname(dirname(path))

print "installing in prefix", glade3_prefix


copy('kiwiwidgets.xml',
     os.path.join(glade3_prefix, 'share/glade3/catalogs'))
copy('kiwiwidgets.py',
     os.path.join(glade3_prefix, 'lib/glade3/modules'))
