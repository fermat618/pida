# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from pida.utils.addtypes import Enumeration, PriorityList
#from pida.core.testing import test, assert_equal, assert_notequal

from unittest import TestCase

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


class PriorityListTest(TestCase):

    def test_list(self):
        pl = PriorityList(1, 2, 3)
        self.assertEqual(pl, [1, 2, 3])
        pl.sort(reverse=True)
        self.assertEqual(pl, [3, 2, 1])
        pl.add(4)
        self.assertEqual(pl, [1, 2, 3, 4])
        pl.sort(reverse=True)
        self.assertEqual(pl, [4, 3, 2, 1])

    def test_prio_list(self):
        pl = PriorityList(1, 2, 3, 4, 'test',
                sort_list=(2, 3, 'test', 1, 4))
        self.assertEqual(pl, [2, 3, 'test', 1, 4])

    def test_prio_list2(self):
        pl = PriorityList('test', 1, 2, 3, 4,
                sort_list=(2, 3, 7, 'test', 1, 4, 6))
        self.assertEqual(pl, [2, 3, 'test', 1, 4])
        pl.add(6)
        self.assertEqual(pl, [2, 3, 'test', 1, 4, 6])
        pl.add(7)
        self.assertEqual(pl, [2, 3, 7, 'test', 1, 4, 6])
