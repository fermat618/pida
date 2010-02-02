# -*- coding: utf-8 -*-
"""
    New vim client
    ~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""
import logging
import os, time

import gtk
log = logging.getLogger(__name__)

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop

    mainloop = DBusGMainLoop(set_as_default=True)
except ImportError:
    pass


DBUS_NS = 'uk.co.pida.vim'

def get_bus_name(uid):
    return '.'.join([DBUS_NS, uid])

def get_vim(uid):
    session = dbus.SessionBus()
    for _try in range(10):
        try:
            log.debug('trying vim connect #%s', _try)
            return dbus.Interface(
                    session.get_object(get_bus_name(uid), '/vim'),
                    'uk.co.pida.vim')
        except dbus.DBusException:
            log.debug('vim connect failed, retrying')
            time.sleep(0.1)

def connect_cb(proxy, cb):
    for evt in ['VimEnter', 'VimLeave', 'BufEnter', 'BufDelete', 'BufWritePost',
    'CursorMoved']:
        proxy.connect_to_signal(evt, getattr(cb, 'vim_%s' % evt))

def VimCom(cb, uid):
    proxy = get_vim(uid)
    connect_cb(proxy, cb)
    return proxy



