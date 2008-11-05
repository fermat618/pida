#! /usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys
path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, path)
sys.path.insert(0, os.path.join(path, "externals"))
from pida.utils.pycons import main
args = sys.argv[:]
if './run-pida-pyshell.py' in args:
    args.remove('./run-pida-pyshell.py')
if __file__ in args:
    args.remove(__file__)
main.main(args)
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
