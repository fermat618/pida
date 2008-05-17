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

from pida.core.features import FeaturesConfig

class MyFeatureConfig(FeaturesConfig):

    def create(self):
        self.publish('banana')

class TestFeatureConfig(TestCase):

    def setUp(self):
        self._fc = MyFeatureConfig(self)
        self._fc.create()

    def test_add_feature(self):
        self._fc.publish('banana2')
        self.assert_('banana2' in self._fc)
        self.assert_('banana' in self._fc)

    def test_subscribe_feature(self):
        self._fc.publish('banana')
        self.assert_('banana' in self._fc)
        inst = 123
        self._fc.subscribe('banana', inst)
        self.assert_(123 in self._fc['banana'])
        self.assert_(12 not in self._fc['banana'])

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
