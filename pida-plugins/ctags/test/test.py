import os
from os import path

CONST_A = 1
CONST_B = 2

class Outer(object):
    oav = None

    class Inner(object):
        def inner_a(self):
            pass
        def inner_b(self):
            pass

    def outer_a(self):
        pass
