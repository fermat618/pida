# -*- coding: utf-8 -*- 
"""
    Dbus integration
    ~~~~~~~~~~~~~~~~

    Base classes for integrating services/plugins with DBUS.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import os
from functools import partial

try:
    import dbus

    from dbus.mainloop.glib import DBusGMainLoop
    DBusMainloop = DBusGMainLoop(set_as_default=True)
    
    from dbus.service import Object

    has_dbus = True
    
except ImportError:
    has_dbus = False
    Object = object

class DbusConfigReal(Object):

    def __init__(self, service):
        self.svc = service
        if hasattr(self, 'export_path'):
            ns = DBUS_PATH(service.get_name(), self.export_path)
        else:
            ns = DBUS_PATH(service.get_name())
        Object.__init__(self, BUS_NAME, ns)

class DbusConfigNoop(object):

    def __init__(self, service):
        pass

if has_dbus:

    from pida.utils.pdbus import (UUID, DBUS_PATH, DBUS_NS, EXPORT, 
        SIGNAL, BUS_NAME, BUS)
    from dbus.mainloop.glib import DBusGMainLoop

    DBusMainloop = DBusGMainLoop(set_as_default=True)


    # export the PIDA UUID to the environment for 

    os.environ['PIDA_DBUS_UUID'] = UUID

    DbusConfig = DbusConfigReal
else:
    # noop DbusConfig
    def noop(*args, **kwargs):
        return []

    def nowrapper(*args, **kwargs):
        def wrapper(*args, **kwargs):
            pass
        return wrapper
    
    UUID = None
    DBUS_PATH = noop
    DBUS_NS = noop
    EXPORT = nowrapper
    SIGNAL = nowrapper
    BUS_NAME = None
    BUS = None
    DbusConfig = DbusConfigNoop

