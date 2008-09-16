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
            ns = DBUS_PATH(service.get_label().lower(), self.export_path)
        else:
            ns = DBUS_PATH(service.get_label().lower())
        Object.__init__(self, BUS_NAME, ns)


