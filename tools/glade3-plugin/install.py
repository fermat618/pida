from os.path import join
import subprocess, sys, os

pipe = subprocess.Popen(['which', 'glade-3'], stdout=subprocess.PIPE)
sto = pipe.communicate()[0]
if pipe.returncode:
    print "glade-3 not found in path"

glade3_prefix = sto.strip()[:len('bin/glade-3')-1]

print "installing in prefix %s" %glade3_prefix


subprocess.call(["cp", 'kiwiwidgets.xml', 
          os.path.join(glade3_prefix, 'share', 'glade3', 'catalogs')])
subprocess.call(["cp", 'kiwiwidgets.py',
          os.path.join(glade3_prefix, 'lib', 'glade3', 'modules')])
