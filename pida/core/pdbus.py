# -*- coding: utf-8 -*- 

# Copyright (c) 2008 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

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

