#! /usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys

path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, path)
sys.path.insert(0, os.path.join(path, "externals"))
from pida.core import application
os.environ['PIDA_PATH'] = os.path.dirname(os.path.dirname(
                                os.path.abspath(application.__file__)))

# hack the wm_class so we don't show up as run-pida.py
try:
    import gtk.gdk, glib
    gtk.gdk.set_program_class('Pida')
    glib.set_prgname('pida')
except ImportError:
    pass

application.main()

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
