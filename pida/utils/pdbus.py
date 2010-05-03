# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from functools import partial, wraps
import os

import dbus
from dbus.service import BusName
from dbus.lowlevel import MethodCallMessage
from pida.utils.serialize import loads

DBUS_NS_PREFIX = 'uk.co.pida.pida'
DBUS_PATH_PREFIX = '/uk/co/pida/pida'

BUS = dbus.SessionBus()
UUID = "p" + str(os.getpid())

def DBUS_NS(*path):
    return ".".join((DBUS_NS_PREFIX, ) + path)

def DBUS_PATH(*path, **kwargs):
    return "/".join((DBUS_PATH_PREFIX,) + path)


def _dbus_decorator(f, ns=None, suffix=None):
    @wraps(f)
    def wrapper(*args, **kwds):
        if ns is None:
            namespace = DBUS_NS(kwds.get('suffix', suffix))
        else:
            namespace = ns
        if 'suffix' in kwds:
            del kwds['suffix']

        return f(namespace, *args, **kwds)
    return wrapper

#EXPORT = partial(dbus.service.method, DBUS_NS())
#SIGNAL = partial(dbus.service.signal, DBUS_NS())

EXPORT = partial(_dbus_decorator, dbus.service.method)
SIGNAL = partial(_dbus_decorator, dbus.service.signal)

def rec_pida_pong(*args):
    global _ACTIVE_PIDAS
    _ACTIVE_PIDAS[str(args[0])] = args



def list_pida_bus_names(include_self=False):
    session = dbus.SessionBus()
    bus_names = map(str, session.list_names())
    return [ name for name in bus_names 
             if 'pida.pida' in name and
             (include_self or UUID not in name) ]

def list_pida_instances(include_this=False, timeout=1):
    """
    Return a tuple of running pida session identifiers.
    Each of this identifiers can be used to connect to a remote Pida
    instance
    """

    pida_names = list_pida_bus_names(include_self=include_this)

    session = dbus.SessionBus()
    result = []
    for name in pida_names:
        #XXX: this is sync, that may be evil
        # we asume that only active and 
        # working instances expose the object
        try:
            app = session.get_object(
                name,
                '/uk/co/pida/pida/appcontroller',
                )
            stat = app.get_instance_status(timeout=1)
            result.append(loads(stat))
        except:
            #XXX: log
            print 'failed to aks state of', name
    return result




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
        elif pid[0] == ":":
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

        ns = fpath.replace("/", ".")[1:]

        if 'signature' in kwargs:
            sig = kwargs['signature']
        else:
            sig = MethodCallMessage.guess_signature(*args)

        return self._conn.call_blocking(self._bus_name,
                                 fpath, 
                                 ns,
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

        ns = fpath.replace("/", ".")[1:]

        if 'signature' in kwargs:
            sig = kwargs['signature']
        else:
            sig = MethodCallMessage.guess_signature(*args)

        reply_handler = kwargs.pop('reply_handler', None)
        error_handler = kwargs.pop('error_handler', None)

        return self._conn.call_async(self._bus_name,
                                 fpath, 
                                 ns,
                                 method_name,
                                 sig,
                                 args,
                                 reply_handler,
                                 error_handler,
                                 **kwargs)
