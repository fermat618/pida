from unittest import TestCase

from pida.core.plugins import Registry, NamedSets, \
        StrictNamedSets, DynamicNamedSets, ExtensionPoint, \
        Plugin, PluginFactory, SingletonError, ExtensionPointError, \
        FactoryDict

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

    def test_plugin_from_singleton(self):
        self.reg_singleton()
        got = self.reg.get_plugin_from_singleton(ISingleton)
        self.assertEqual(type(got),Plugin)

    def test_pluin_from_unknown_singleton_fail(self):
        self.assertRaises(
                SingletonError,
                lambda: self.reg.get_plugin_from_singleton(ISingleton))

    def test_clear_registry(self):
        self.reg_singleton()
        self.reg.clear()
    
    def test_ext_points_get(self):
        self.reg_singleton()
        self.reg.ext_points["test"]


def gen_data(sets):
    sets.add("job", "manager")
    sets.add("name", "josh")


class TestNamedSets(TestCase):
    def setUp(self):
        self.sets=NamedSets()
    
    def test_fail_getitem(self):
        self.assertRaises(NotImplementedError,
                lambda:self.sets["test"])
    
    def test_fail_add(self):
        self.assertRaises(NotImplementedError,
            lambda:self.sets.add("test","test"))
        
    def test_fail_remove(self):
        self.assertRaises(NotImplementedError,
            lambda:self.sets.remove("test","test"))

class TestDynamicNamedSets(TestCase):
    
    def setUp(self):
        self.sets = DynamicNamedSets()
    
    def test_repr(self):
        self.assertEqual(repr(self.sets),"{}")
    
    def test_add(self):
        gen_data(self.sets)
    
    def test_remove(self):
        gen_data(self.sets)
        self.sets.remove("name", "josh")
        self.failIf("name" in self.sets.data)
    
    def test_remove_unknown(self):
        self.sets.remove("name", "josh")
    
    def test_delitem(self):
        gen_data(self.sets)
        del self.sets["name"]
        self.failIf("name" in self.sets.data)

    def test_delitem_unknown(self):
        del self.sets["name"]

class TestStrictNamedSets(TestCase):
    def setUp(self):
        self.sets=StrictNamedSets(("name","job"))
    
    def test_create(self):
        self.assertEqual(
                repr(StrictNamedSets(("test",))),
                "{'test': set([])}")

    def test_add(self):
        gen_data(self.sets)
    
    def test_getitem(self):
        self.assertEqual(self.sets["name"], set([]))

    def test_remove(self):
        gen_data(self.sets)
        self.sets.remove("name","josh")
        self.assertEqual(self.sets["name"], set([]))

class TestExtensionPoint(TestCase):
    def setUp(self):
        self.p = ExtensionPoint()


    def test_init(self):
        gen_data(self.p)
        self.p.init_extensions(["name"])
        self.failIf(hasattr(self.p, "lazy"))


    def test_uninit_fail_getitem(self):
        def test():
            self.p["name"]
        self.assertRaises(
                ExtensionPointError, 
                test)
        
    def test_uninit_fail_keys(self):
        self.assertRaises(ExtensionPointError, self.p.keys)
    
    def test_keys(self):
        gen_data(self.p)
        self.p.init_extensions(["name"])
        self.assertEqual(
                self.p.keys(),
                ["name"])
    
class TestPluginFactory(TestCase):
    def test_need_params(self):
        self.assertRaises(TypeError,PluginFactory)


class TestPlugin(TestCase):
    def setUp(self):
        self.pstr=Plugin(factory=str)
        self.pin=Plugin(instance="test")
    
    def test_create_fail_factory(self):
        self.assertRaises(TypeError,lambda: Plugin(factory=""))

    def test_factory(self):
        self.assertEqual(self.pstr.get_instance("test"),"test")
    
    def test_reset_factory(self):
        self.pstr.reset()

class TestFactoryDict(TestCase):
    def setUp(self):
        self.dict=FactoryDict(str.upper)
    
    def test_gen(self):
        self.assertEqual(self.dict["test"],"TEST")
        self.assertEqual(self.dict.data.keys(),["test"])
        del self.dict["test"]
