# -*- coding: utf-8 -*-
# license: gnu gpl 2+
from unittest import TestCase

from pida.core.commands import CommandsConfig

class MyCommands(CommandsConfig):

    def do_something(self):
        self.svc.something_done = True

    def do_another(self, banana):
        self.svc.another = banana

    def do_one_more(self):
        return 12345

class TestCommandConfig(TestCase):

    def setUp(self):
        self.something_done = False
        self.another = None
        self.com = MyCommands(self)

    def test_basic_call(self):
        self.assertEqual(self.something_done, False)
        self.com.do_something()
        self.assertEqual(self.something_done, True)

    def test_named_call(self):
        self.assertEqual(self.something_done, False)
        self.com('do_something')
        self.assertEqual(self.something_done, True)

    def test_argument(self):
        self.assertEqual(self.another, None)
        self.com('do_another', banana='melon')
        self.assertEqual(self.another, 'melon')

    def test_error_non_kw(self):
        def c():
            self.com('do_another', 'melon')
        self.assertRaises(TypeError, c)

    def test_return_val(self):
        self.assertEqual(self.com('do_one_more'), 12345)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
