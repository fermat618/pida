# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from functools import partial, wraps


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

_ACTIVE_PIDAS = {}
_CALLBACKS = {}

def rec_pida_pong(*args):
    global _ACTIVE_PIDAS
    _ACTIVE_PIDAS[str(args[0])] = args


def list_pida_instances(include_this=False, callback=None, callback_done=None,
                        ext=True, timeout=1, block=False):
    """
    Return a tuple of running pida session identifiers.
    Each of this identifiers can be used to connect to a remote Pida
    instance
    """
    global _ACTIVE_PIDAS
    if not callback:
        callback = rec_pida_pong
        _ACTIVE_PIDAS = {}
    if ext:
        pong = 'PONG_PIDA_INSTANCE_EXT'
        ping = 'PING_PIDA_INSTANCE_EXT'
    else:
        pong = 'PONG_PIDA_INSTANCE'
        ping = 'PING_PIDA_INSTANCE'
    session = dbus.SessionBus()
    
    if not _CALLBACKS.has_key(rec_pida_pong):
        _CALLBACKS[rec_pida_pong] = session.add_signal_receiver(
            rec_pida_pong, pong, dbus_interface=DBUS_NS('appcontroller'))
    
    if not _CALLBACKS.has_key(callback):
        # this is ugly but needed to prevent multi registration
        _CALLBACKS[callback] = session.add_signal_receiver(
            callback, pong, dbus_interface=DBUS_NS('appcontroller'))
    m = dbus.lowlevel.SignalMessage('/', DBUS_NS('appcontroller'), ping)

    if block:
        # this is ugly, but blocking calls with send_message doesn't work
        import gtk

        def gq(rep):
            gtk.main_quit()

        session.send_message_with_reply(m, gq, timeout)

        gtk.main()
        return _ACTIVE_PIDAS.values()
    if callback_done:
        session.send_message_with_reply(m, callback_done, timeout)
    else:
        session.send_message(m)

    return None


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

        if kwargs.has_key('signature'):
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

        if kwargs.has_key('signature'):
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
