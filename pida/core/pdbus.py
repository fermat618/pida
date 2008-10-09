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

import dbus
from dbus.service import Object

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

from pida.utils.pdbus import UUID, DBUS_PATH, DBUS_NS, EXPORT, SIGNAL, BUS_NAME


# export the PIDA UUID to the environment for 

os.environ['PIDA_DBUS_UUID'] = UUID

class DbusConfig(Object):

    def __init__(self, service):
        self.svc = service
        if hasattr(self, 'export_path'):
            ns = DBUS_PATH(service.get_name(), self.export_path)
        else:
            ns = DBUS_PATH(service.get_name())
        Object.__init__(self, BUS_NAME, ns)


