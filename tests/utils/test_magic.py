DO_STRESS = False

from unittest import TestCase
from threading import Thread
from pida.utils.magic import Magic
import os

class MagicRun(Thread):
    def __init__(self, top):
        self.top = top
        super(MagicRun, self).__init__()

    def run(self):
        for dirname, dirs, files in os.walk(self.top):
            for fname in files:
                ma = Magic(mime=True)
                ma.from_file(os.path.join(dirname, fname))
                ma = Magic(mime=False)
                ma.from_file(os.path.join(dirname, fname))

class TestMagic(TestCase):
    def test_stress(self):
        if not DO_STRESS:
            return
        threads = []
        top = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "pida")
        for i in range(10):
            thr = MagicRun(top)
            threads.append(thr)
            thr.start()
        for thr in threads:
            thr.join()
