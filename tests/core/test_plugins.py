from unittest import TestCase

from pida.core.plugins import Registry, NamedSets, \
        StrictNamedSets, DynamicNamedSets, ExtensionPoint, \
        Plugin, SingletonError

class ISingleton:
    """A singleton definition"""


class IFeature:
    """A feature definition"""


class Singleton(object):
    """Singleton Implementation"""
    def __init__(self, registry=None):
        pass


class TestSingleton(TestCase):
    
    def reg_singleton(self,**kw):
        s = Singleton()
        self.reg.register_plugin(
            instance=s,
            singletons=(ISingleton,),
            **kw
            )
        return s


    def setUp(self):
        self.reg = Registry()

    def test_register_instance(self):
        s = self.reg_singleton()
        assert self.reg.get_singleton(ISingleton) is s

    def test_register_factory(self):
        s = Singleton
        self.reg.register_plugin(
            factory=s,
            singletons=(ISingleton,)
            )
        self.assertEqual(type(self.reg.get_singleton(ISingleton)),s)

    def test_duplicate_singleton_error(self):
        self.reg_singleton()
        self.assertRaises(SingletonError, self.reg_singleton)
    
    def test_unregister_singleton(self):
        self.reg_singleton()
        self.reg.unregister_singleton(ISingleton)

    def test_unregsiter_singleton_unknown(self):
        def test():
            self.reg.unregister_singleton(ISingleton)
        self.assertRaises(SingletonError,test)

    def test_register_with_feature(self):
        self.reg_singleton(features=(IFeature,))

    def test_uregister_with_feature(self):
        self.reg_singleton(features=(IFeature,))
        plugin = list(self.reg)[0]
        self.reg.unregister_feature(IFeature,plugin)
    
    def test_iter(self):
        plugin = self.reg_singleton()
        self.assertEqual(list(self.reg)[0].get_instance(None),plugin)


    def test_clear_registry(self):
        self.reg_singleton()
        self.reg.clear()
