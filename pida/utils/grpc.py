# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

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

# gobject import
import gobject

# system imports
import os
import socket
import cPickle

from kiwi.utils import gsignal


class NotStartedError(RuntimeError):
    """Reactor has not yet been started"""


class Reactor(gobject.GObject):

    gsignal('received', str, int, str, object)

    def __init__(self, port, host=''):
        gobject.GObject.__init__(self)
        self.host = host
        self.port = port
        self.socket = None
         
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        gobject.io_add_watch(self.socket, gobject.IO_IN, self._on_socket_read)
    
    def stop(self):
        pass
        #os.unlink(self.socketfile)

    def call_local(self, host, port, command, args):
        print host, port, command, args
        self.emit('received', host, port, command, args)

    def call_remote(self, host, port, command, args):
        self._send(host, port, self._encode_msg(command, args))

    def _on_socket_read(self, socket, condition):
        if condition == gobject.IO_IN:
            data, (host, port) = socket.recvfrom(6024)
            self._received_data(data, host, port)
        return True

    def _send(self, host, port, data):
        if self.socket is None:
            raise NotStartedError
        self.socket.sendto(data, (host, port))

    def _encode_msg(self, command, args):
        return cPickle.dumps((command, args))

    def _decode_msg(self, msg):
        return cPickle.loads(msg)

    def _received_data(self, data, host, port):
        self.call_local(host, port, *self._decode_msg(data))


class ServerReactor(Reactor):

    """A server"""

    def __init__(self, port, host=''):
        Reactor.__init__(self, port, host)
        self.start()


class LocalServerReactor(ServerReactor):
    
    """A local only server"""

    def __init__(self, port):
        ServerReactor.__init__(self, port, '127.0.0.1')


class ClientReactor(Reactor):

    """A Client"""

    def __init__(self, remote_port, remote_host):
        Reactor.__init__(self, 0)
        self.r_host = remote_host
        self.r_port = remote_port
        self.start()

    def call_server(self, command, args):
        Reactor.call_remote(self, self.r_host, self.r_port, command, args)
        

class LocalClientReactor(ClientReactor):
    
    """A local only client"""

    def __init__(self, remote_port):
        ClientReactor.__init__(self, remote_port, '127.0.0.1')


class Dispatcher(object):

    def __init__(self, reactor):
        self.reactor = reactor
        self.reactor.connect('received', self._on_received)

    def _on_received(self, reactor, host, port, command, args):
        command_name = 'remote_%s' % command
        command_call = getattr(self, command_name, None)
        if command_call is not None:
            command_call(*args)
            if command not in ['error', 'ok']:
                self.call_remote(host, port, 'ok', (command,))
        else:
            self.call_remote(host, port, 'error', (command,))

    def call_remote(self, host, port, command, args):
        self.reactor.call_remote(host, port, command, args)

    def remote_ok(self, command):
        print 'OK', command

    def remote_error(self, command):
        print 'ERROR', command


class LocalServerDispatcher(Dispatcher):

    def __init__(self, port):
        Dispatcher.__init__(self, LocalServerReactor(port))


class LocalClientDispatcher(Dispatcher):

    def __init__(self, remote_port):
        Dispatcher.__init__(self, LocalClientReactor(remote_port))

    def call_server(self, command, args):
        self.reactor.call_server(command, args)


gobject.type_register(Reactor)

if __name__ == '__main__':
    import sys
    if sys.argv[-1] == 'c':
        r = LocalClientDispatcher(9000)
        print 'client'
        r.call_server('hello', ())
        import gtk
        gtk.main()
    else:
        r = LocalServerDispatcher(9000)
        import gtk
        gtk.main()








# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
