from unittest import TestCase
from pida.utils.unique import counter

class TestPath(TestCase):

    def test_counter(self):
        c = counter()
        for i in xrange(1, 11):
            self.assertEqual(c(), i)
        c2 = counter()
        for i in xrange(1, 11):
            self.assertEqual(c2(), i)
        for i in xrange(11, 21):
            self.assertEqual(c(), i)
