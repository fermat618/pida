

"""
New vim client.
"""
import os, time

import gtk, dbus

from dbus.mainloop.glib import DBusGMainLoop

mainloop = DBusGMainLoop(set_as_default=True)

DBUS_NS = 'uk.co.pida.vim'

def get_object_path(uid):
    return '/uk/co/pida/vim/%s' % uid

def get_vim(uid):
    session = dbus.SessionBus()
    proxy = None
    while proxy is None:
        try:
            proxy = session.get_object(DBUS_NS, get_object_path(uid))
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



