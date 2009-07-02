# -*- coding: utf-8 -*-
"""
    The moo Editor
    ~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""

MAPPINGS = {}

def build_mapping(langmgr, docmanager):
    global MAPPINGS
    for lang in langmgr.get_available_langs():
        for data in docmanager.itervalues():
            lmatch = lang.props.name.lower() 
            if lmatch == data.internal.lower() or \
               lmatch == data.human.lower() or \
               any((lmatch == x.lower() for x in data.aliases)):
                MAPPINGS[data.internal] = lang
                data.inc_support()

