# -*- coding: utf-8 -*-

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
