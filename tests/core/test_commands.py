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

# Standard Library Imports
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
