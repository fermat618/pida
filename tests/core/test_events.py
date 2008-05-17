# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:


from pida.core.events import EventsConfig
import unittest

class MockCallback(object):

    def __init__(self):
        self.calls = []

    def __call__(self, **kw):
        self.calls.append(kw)

class EventTestCase(unittest.TestCase):

    def setUp(self):
        self.e = EventsConfig(None)
        self.c = MockCallback()
        self.e.publish('initial')
        self.e.subscribe('initial', self.c)

    def test_emit_event(self):
        self.e.emit('initial')
        self.assertEqual(len(self.c.calls) , 1)
        self.assertEqual(self.c.calls[0], {})

    def test_emit_event_multiple(self):
        self.e.emit('initial')
        self.e.emit('initial')
        self.e.emit('initial')
        self.assertEqual(len(self.c.calls) , 3)

    def test_emit_event_with_argument(self) :
        self.e.emit('initial', parameter=1)
        self.assertEqual(len(self.c.calls) , 1)
        self.assertEqual(self.c.calls[0], {'parameter': 1})

    def test_emit_event_bad_argument(self):
        try:
            self.e.emit('initial', 1)
            raise AssertionError('TypeError not raised')
        except TypeError:
            pass

