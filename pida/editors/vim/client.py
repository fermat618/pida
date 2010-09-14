# -*- coding: utf-8 -*-
"""
    New vim client
    ~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""
import os, time

import gtk
import logbook
log = Logbook.Logger('Pida Vim Client')

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop

    mainloop = DBusGMainLoop(set_as_default=True)
except ImportError:
    pass


DBUS_NS = 'uk.co.pida.vim.{uid}'

def get_vim(uid):
    name = DBUS_NS.format(uid=uid)
    session = dbus.SessionBus()
    def cb(bn):
        if bn: # may be empty
            gtk.main_quit()
    watch = session.watch_name_owner(name, cb)
    gtk.main() #XXX: this might kill us if vim somehow fails
    try:
        log.info('trying to connect to {name}', name=name)
        return dbus.Interface(
                session.get_object(name, '/vim'),
                'uk.co.pida.vim')
    except dbus.DBusException:
        log.info('connect failed')
        raise SystemExit('vim failed')

