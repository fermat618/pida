
from pida.core.boss import Boss

from unittest import TestCase

class BossTest(TestCase):

    def setUp(self):
        self._b = Boss(None)
        
    def test_start(self):
        return
        #self._b.start()

    def test_stop(self):
        self._b.stop()
