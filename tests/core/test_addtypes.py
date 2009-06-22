# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import os
from pida.utils.addtypes import Enumeration
#from pida.core.testing import test, assert_equal, assert_notequal

from pida.utils.testing.mock import Mock

from unittest import TestCase
from tempfile import mktemp

class EnumerationTest(TestCase):

    def test_enum(self):
        test = Enumeration('test', ('A', 'B', 'C'))
        self.assertEqual(test.A, 0)
        self.assertEqual(test.B, 1)
        self.assertEqual(test.C, 2)
    
    def test_tupel(self):
        test = Enumeration('test', (('A', 1), ('B', 0), ('C', 10)))
        self.assertEqual(test.A, 1)
        self.assertEqual(test.B, 0)
        self.assertEqual(test.C, 10)

    def test_change(self):
        test = Enumeration('test', ('A', 'B', 'C'))
        self.assertEqual(test.A, 0)
        self.assertRaises(AttributeError, setattr, test, 'A', 5)
        self.assertRaises(AttributeError, setattr, test, 'X', 9)

    def test_missing(self):
        test = Enumeration('test', ('A', 'B', 'C'))
        self.assertRaises(AttributeError, getattr, test, 'D')
