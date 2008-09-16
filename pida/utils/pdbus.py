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

from functools import partial

import dbus
from dbus.service import BusName
from dbus.lowlevel import MethodCallMessage

DBUS_NS_PREFIX = 'uk.co.pida.pida'
DBUS_PATH_PREFIX = '/uk/co/pida/pida'

BUS = dbus.SessionBus()
UUID = "p" + BUS.get_unique_name()[1:].replace(".","_")

def DBUS_NS(*path):
    return ".".join((DBUS_NS_PREFIX, ) + path)

def DBUS_PATH(*path, **kwargs):
    return "/".join((DBUS_PATH_PREFIX,) + path)

BUS_NAME = BusName(DBUS_NS(UUID), bus=dbus.SessionBus())

EXPORT = partial(dbus.service.method, DBUS_NS())
SIGNAL = partial(dbus.service.signal, DBUS_NS())


def list_pida_instances(include_this=False):
    """
    Return a tuple of running pida session identifiers.
    Each of this identifiers can be used to connect to a remote Pida
    instance
    """
    session = dbus.SessionBus()
    rv = []
    for x in session.list_names(): 
        if x[:len(DBUS_NS_PREFIX)] == DBUS_NS_PREFIX:
            match = x[len(DBUS_NS_PREFIX)+1:]
            if not len(match):
                continue
            if not include_this and match == UUID:
                continue
            rv.append(match)
    return rv

class PidaRemote(object):
    """
    Constructs a proxy object to a remote pida instance
    """
    def __init__(self, pid, 
                    object_path=(),
                    conn=dbus.SessionBus(), 
                    bus_name=None):

        self._path = DBUS_PATH(*object_path)
        assert len(pid)
        # pid seem to be of 
        if pid[0] == "p":
            pid = ":" + pid[1:].replace("_", ".")
            self._bus_name = pid
        else:
            if not bus_name:
                self._bus_name=DBUS_NS(pid)
            else:
                self._bus_name=bus_name
            
        self._pid = pid
        self._conn = conn

    def call(self, path, method_name, *args, **kwargs):
        """Calls a method with method_name under the subpath of path"""

        if path:
            fpath = "%s/%s" %(self._path, path)
        else:
            fpath = self._path

        if kwargs.has_key('signature'):
            sig = kwargs['signature']
        else:
            sig = MethodCallMessage.guess_signature(*args)

        return self._conn.call_blocking(self._bus_name,
                                 fpath, 
                                 DBUS_NS_PREFIX,
                                 method_name,
                                 sig,
                                 args,
                                 **kwargs)


    def call_async(self, path, method_name, *args, **kwargs):
        """
        Calls a method with method_name under the subpath of path async.

        The reply_handler and error_handler keyword arguments are 
        called on success or error.

        """

        if path:
            fpath = "%s/%s" %(self._path, path)
        else:
            fpath = self._path

        if kwargs.has_key('signature'):
            sig = kwargs['signature']
        else:
            sig = MethodCallMessage.guess_signature(*args)

        reply_handler = kwargs.get('reply_handler', None)
        error_handler = kwargs.get('error_handler', None)

        return self._conn.call_async(self._bus_name,
                                 fpath, 
                                 DBUS_NS_PREFIX,
                                 method_name,
                                 sig,
                                 args,
                                 reply_handler,
                                 error_handler,
                                 **kwargs)

