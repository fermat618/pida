#! /usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys
path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, path)
from pida.core.application import main
main()

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
