from unittest import TestCase

from pida.core.plugins import Registry

class ISingleton:
    """A singleton definition"""


class IFeature:
    """A feature definition"""


class Singleton(object):
    """Singleton Implementation"""
    def __init__(self, registry=None):
        pass


class TestSingleton(TestCase):

    def setUp(self):
        self.reg = Registry()

    def test_register_instance(self):
        s = Singleton()
        self.reg.register_plugin(
            instance=s,
            singletons=(ISingleton,)
        )
        assert self.reg.get_singleton(ISingleton) is s

    def test_register_factory(self):
        s = Singleton
        self.reg.register_plugin(
            factory=s,
            singletons=(ISingleton,)
        )
        assert isinstance(self.reg.get_singleton(ISingleton), s)

    def test_duplicate_singleton_error(self):
        def reg():
            s = Singleton()
            self.reg.register_plugin(
                instance=s,
                singletons=(ISingleton,)
            )
        reg()
        self.assertRaises(Exception, reg)

        

