# -*- coding: utf-8 -*-
"""
    New vim client
    ~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""
import os, time

import gtk, dbus

from dbus.mainloop.glib import DBusGMainLoop

mainloop = DBusGMainLoop(set_as_default=True)

DBUS_NS = 'uk.co.pida.vim'

def get_bus_name(uid):
    return '.'.join([DBUS_NS, uid])

def get_vim(uid):
    session = dbus.SessionBus()
    proxy = None
    while proxy is None:
        try:
            proxy = session.get_object(get_bus_name(uid), '/vim')
        except dbus.DBusException:
            proxy = None
            time.sleep(0.2)
    print proxy
    return proxy

def connect_cb(proxy, cb):
    for evt in ['VimEnter', 'VimLeave', 'BufEnter', 'BufDelete', 'BufWritePost',
    'CursorMoved']:
        proxy.connect_to_signal(evt, getattr(cb, 'vim_%s' % evt))

def VimCom(cb, uid):
    proxy = get_vim(uid)
    connect_cb(proxy, cb)
    return proxy



