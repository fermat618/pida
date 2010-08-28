# -*- coding: utf-8 -*-
"""
    The debug utilities

    :copyright: 2009 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

def srvs():
    """make a global reference to all services"""
    for srv in boss.get_services():
        globals()[srv.get_name()] = srv
