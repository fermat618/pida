# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:


import pida.core.event as event
import unittest

class MockCallback(object):

    def __init__(self):
        self.count = 0
        self.args = []
        self.kw = {}

    def cb(self, *args, **kw):
        self.count = self.count + 1
        self.args = args
        self.kw = kw
        return True

def c():
    return event.event(), MockCallback()


class EventTestCase(unittest.TestCase):

    def setUp(self):
        self.e = event.event()
        self.__dummycount = 0
        self.__dummyargs = []
        self.__dummykw = {}

    def test_create_event(self):
        e, cb = c()
        self.assertEqual(e.has_event('banana'), False)
        e.create_event('banana')
        self.assertEqual(e.has_event('banana'), True)

    def test_register_callback(self):
        e, cb = c()
        e.create_event('banana')
        e.register('banana', cb.cb)

    def test_emit_event(self):
        e, cb = c()
        e.create_event('banana')
        e.register('banana', cb.cb)
        self.assertEqual(cb.count, 0)
        e.emit('banana')
        self.assertEqual(cb.count, 1)
        self.assertEqual(cb.args, ())
        self.assertEqual(cb.kw, {})

    def test_emit_event_multiple(self):
        e, cb = c()
        e.create_event('banana')
        e.register('banana', cb.cb)
        self.assertEqual(cb.count, 0)
        e.emit('banana')
        self.assertEqual(cb.count, 1)
        e.emit('banana')
        self.assertEqual(cb.count, 2)
        e.emit('banana')
        self.assertEqual(cb.count, 3)
        
    def test_emit_event_with_argument(self):
        e, cb = c()
        e.create_event('banana')
        e.register('banana', cb.cb)
        self.assertEqual(cb.count, 0)
        e.emit('banana')
        self.assertEqual(cb.count, 1)
        e.emit('banana', parameter=1)
        self.assertEqual(cb.count, 2)
        self.assertEqual(cb.args, ())
        self.assertEqual(cb.kw, {'parameter': 1})
        
    def test_emit_event_bad_argument(self):
        e, cb = c()
        e.create_event('banana')
        e.register('banana', cb.cb)
        try:
            e.emit('banana', 1)
            raise AssertionError('TypeError not raised')
        except TypeError:
            pass

