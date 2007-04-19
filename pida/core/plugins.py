"""A flexible plugin framework.

Clear your mind of any previously defined concept of a plugin.

Key components:

    * Registry: stores a set of plugins
    * Plugin: defines a set of behaviours
    * Registry key: unique behavioural identifier

Types of definable behaviour:

    1. Singleton
    2. Feature
    3. Extension Point/Extender

A plugin can register any number of the above behaviour
types.

1. Singleton

When a plugin registers as a singleton for a key, it is saying "I provide the
behaviour", so when the registry is looked up for that key, the object is
returned. At this point, please consider that an ideal registry key may be an
Interface definition (formal or otherwise), so when you ask for the behaviour
by interface you are actually returned an object implementing that interface.

2. Feature

When a plugin defines a Feature, it is again saying "I provide the behaviour",
the difference with singleton is that many plugins can define a feature, and
these plugins are aggregated and can be looked up by registry key. The look up
returns a list of objects that claim to provide the key.

3. Extension point

An extension point is identical to a feature except that the keys for it must
be predefined and are fixed. While a plugin may invent a feature and others
can join it, it is expected that whatever creates the registry formally
defines the extension points and they are then fixed. This can be used to
simulate the behaviour of traditional (Eclipse or Trac) extension points. The
plugin itself supplies the Extender (that which extends), while the registry
contains the Extension point itself (that which is to be extended).

Defining Plugins:

1. Singletons

a. First you will need a registry item:

    reg = Registry()

b. now define a behavioural interface:

    class IAmYellow(Interface):
        def get_shade():
            "get the shade of yellow"

c. now write a class that implements this behaviour:

    class Banana(object):
        def get_shade(self):
            return 'light and greeny'

d. create an instance of the plugin

    plugin = Banana()

e. register it with the registry:

    reg.register_plugin(
            instance=plugin,
            singletons=(IAmYellow,)
        )

f. get the item from the registry at a later time:

    plugin = reg.get_singleton(IAmYellow)
    print plugin.get_shade()

Things to note:

    * Attempting to register another plugin with a singleton of IAmYellow will
      fail.

    * Looking up a non-existent singleton will raise a SingletonError.


"""

import weakref

##############################################################################
## Core data types

def copy_docs(cls):
    def decorator(func):
        func.__doc__ = getattr(cls, func.__name__).__doc__
        return func
    return decorator
    
class NamedSets(object):
    """
    The theory of the plugin architecture has its foundations
    on this simple structure which is a simple collection of named sets.
    
    Each key is associated to a set and the available operations are: to add
    elements to the named set or to remove them.
    """
    def __getitem__(self, name):
        """
        Returns the named set.
        
        @param name: the name of the set
        @return: an iterator to the named set.
        """
        raise NotImplementedError
    
    def add(self, name, value):
        """
        Add one one value to the named set.
        
        @param name: the name of the set
        @param value: the value to be added to the set
        """
        raise NotImplementedError
    
    def remove(self, name, value):
        """
        Remove the `value` from the set named `name`.
        
        @param name: the name of the set to remove the value from
        @param value: the value to remove from the named set
        """
        raise NotImplementedError
        
    def keys(self):
        """
        Return a collection of the names of the existing sets.
        """
        return self.data.keys()
    
    names = keys
    
    def __delitem__(self, name): 
        """
        Remove the named set.
        
        @param name: the name of the set to be removed.
        """
        del self.data[name]

    @copy_docs(list)
    def __repr__(self):
        return "<%s: %r>"%(
                self.__class__.__name__,
                self.data
                )
    @copy_docs(list)
    def __len__(self):
        return len(self.data)

    @copy_docs(list)
    def __iter__(self):
        return iter(self.data)



class StrictNamedSets(NamedSets):
    """
    A strict named sets is a `NamedSets` that has fixed predefined sets.
    
    In order to access a set, for adding or removing elements, you must
    initialize it first. Trying to perform an operation on a undefined named
    set will result in a `KeyError`.
    """
    def __init__(self, names=()):
        """
        Creates a strict named sets by providing an optional number of keys
        to define.
        
        @param names: the sets to initialize.
        """
        self.data = dict((name, set()) for name in set(names))
        

    @copy_docs(NamedSets)
    def __getitem__(self, name):
        return self.data[name]
        
    @copy_docs(NamedSets)
    def add(self, key, value):
        self.data[key].add(value)

    @copy_docs(NamedSets)
    def remove(self, key, value):
        return self.data[key].discard(value)


class DynamicNamedSets(NamedSets):
    """
    In a dynamic named set the sets are created (empty sets) when you access
    them.
    """
    
    def __init__(self):
        """Creates an empty dynamic named sets object."""
        self.data = {}
        
    @copy_docs(NamedSets)
    def __getitem__(self, key):
        return self.data.get(key, ())
    
    @copy_docs(NamedSets)
    def remove(self, key, value):
        key_set = self.data.get(key, None) 
        if key_set is not None:
            key_set.discard(value)
            if not key_set:
                del self.data[key]
        return value
    
    @copy_docs(NamedSets)
    def add(self, key, value):
        self.data.setdefault(key, set()).add(value)

    @copy_docs(NamedSets)
    def __delitem__(self, key):
        self.data.pop(key, None)

    @copy_docs(dict)
    def clear(self):
        self.data.clear()

##############################################################################
## Base classes

class Plugin(object):
    """A possible implementation of a Plugin. A plugin holds an object.
    When the 'get_instance' method is called, by suplying a registry, the
    held object is returned. If you extend `Plugin` you can change this
    by suplying one instance for an appropriate registry, or generating an
    instance every time the method is called.
    
    You can create a plugin's instance by issuing an `instance` or a `factory`
    function. The factory function receives an argument, the context registry
    and returns the object this plugin holds. If you use the factory it is
    called only once, to set the holded object, when the `get_instance` 
    method is called.
    """
    def __init__(self, instance=None, factory=None):
        if factory is not None and not callable(factory):
            raise TypeError("If you specify a factory it must be a callable object.", factory)
            
        if factory is None:
            self.instance = instance
        else:
            self.factory = factory
            
    def get_instance(self, registry):
        """Returns the object associated with the `Plugin`."""
        try:
            return self.instance
        except AttributeError:
            self.instance = self.factory(registry)
            return self.instance

    def reset(self):
        """When this plugin contains a factory makes it regen the instance."""
        if hasattr(self,"instance"):
            del self.instance

    def unplug(self, registry):
        """This method is called when the service is removed from the registry"""

##############################################################################
## Implementations
class ExtensionPointError(StandardError):
    """Raised when there's an error of some sort"""
    
class ExtensionPoint(object):
    """This class is based on Eclipse's plugin architecture. An extension
    point is a class for defining a number of named sets, we'll address each
    named list an extension. Conceptually an `ExtensionPoint` is a special
    case of a `NamedList`, they have an equal interface.
    
    In order to access extensions we have to initialize the `ExtensionPoint`
    by calling the `init_extensions` method.
    
    Before initializing the `ExtensionPoint` we can add objects in any
    extensions. Objects added before initialization that are contained in an
    extension not initialized will be silentely discarded.
    
    After the `ExtensionPoint` is initialized, when objects are added to an
    extension, they are activated, calling the protected method `_activate`.
    The `_activate` method can be create to mutate objects when they are
    inserted into the extension. Objects added to extensions before the
    `ExtensionPoint` is initialized are only activated when the
    `init_extensions` method is called.
    """
    def __init__(self):
        """Creates a new extension point object."""
        self.lazy = DynamicNamedSets()
    
    def _activate(self, extender):
        """
        This method is called when the object is placed in an initialized
        extension.
        """
        return extender
    
    def init_extensions(self, extension_points):
        """
        Initializes the valid extensions.
        """
        self.data = StrictNamedSets(extension_points)
        
        for ext_pnt in self.lazy:
            try:
                for extender in self.lazy[ext_pnt]:
                    self.data.add(ext_pnt, self._activate(extender))
                
            except KeyError:
                pass
        del self.lazy
       
    @copy_docs(NamedSets)
    def add(self, name, value):
        """Adds one more element to the extension point, or named list."""
        try:
            self.data.add(name, self._activate(value))
        except AttributeError:
            self.lazy.add(name, value)

    @copy_docs(NamedSets)
    def __getitem__(self, key):
        try:
            return self.data[key]
        except AttributeError:
            raise ExtensionPointError("Not initialized, run init() first")

    get_extension_point = __getitem__
    
    def has_init(self):
        """
        Verifies if the extension point was already initialized.
        """
        return hasattr(self, "data")

    @copy_docs(NamedSets)
    def keys(self):
        try:
            return self.data.keys()
        except:
            raise ExtensionPointError("Not initialized, run init() first")
        

class PluginExtensionPoint(ExtensionPoint):
    """This is an `ExtensionPoint` prepared to hold `Plugin`s."""
    def __init__(self, registry):
        self._registry = weakref.ref(registry)
        ExtensionPoint.__init__(self)
    
    @copy_docs(ExtensionPoint)
    def _activate(self, plugin):
        # in this case we want to hold the actual instance and not the plugin
        return plugin.get_instance(self._registry())


class FactoryDict(object):
    """
    A factory dict is a dictionary that creates objects, once, when they
    are first accessed from a factory supplied at runtime.
    The factory accepts one argument, the suplied key, and generates an object
    to be held on the dictionary.
    """
    
    def __init__(self, factory):
        """
        Creates a `FactoryDict` instance with the appropriate factory
        function.
        
        @param factory: the function that creates objects according to the
        supplied key.
        """
        self.data = {}
        self.factory = factory

    @copy_docs(dict)
    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            val = self.data[key] = self.factory(key)
            return val
    
    @copy_docs(dict)
    def __delitem__(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass
    
    @copy_docs(dict)
    def __repr__(self):
        return repr(self.data)

##############################################################################
## Use case of the classes defined above

class SingletonError(StandardError):
    """Raised when you there's a problem related to Singletons."""

class PluginEntry(object):
    def __init__(self, plugin, features, singletons, extension_points, extends):
        self.plugin = plugin
        self.features = list(features)
        self.singletons = list(singletons)
        self.extends = dict(extends)
        self.extension_points = list(extension_points)
    
    def get_instance(self, *args, **kwargs):
        return self.plugin.get_instance(*args, **kwargs)


class PluginFactoryCreator(object):
    """
    This is a factory of plugin factories.
    Instances of this class are the factories needed on `Registry.register`,
    where the only thing you change is the actual `Plugin` factory.
    
    This class is needed when you need to specify a class that extends from
    `Plugin`.
    
    @param singletons: the singletons where the plugin will be registred
    @param features: the features where the plugin will be registred
    @param extends: the extension points the plugin will be registred
    @param extension_points: the extension points this plugins defines
    """
    def __init__(self, plugin_factory):
        self.plugin_factory = plugin_factory

    def __call__(self, **kwargs):
        singletons = kwargs.pop("singletons", ())
        features = kwargs.pop("features", ())
        extends = kwargs.pop("extends", ())
        extension_points = kwargs.pop("extension_points", ())
            
        if len(singletons) == len(features) == 0:
            raise TypeError("You must specify at least one feature or one singleton key")
        plugin = self.plugin_factory(**kwargs)
        return plugin, features, singletons, extension_points, extends


# This is the default factory that uses the class Plugin
PluginFactory = PluginFactoryCreator(Plugin)


class Registry(object):
    def __init__(self, plugin_factory=PluginFactory):
        self.singletons = {}
        self.plugins = {}
        
        self.plugin_factory = plugin_factory
        
        plugin_factory = lambda x: PluginExtensionPoint(self)
        
        self.ext_points = FactoryDict(plugin_factory)
        self.features = DynamicNamedSets()
        
    
    def register(self, plugin, features, singletons, extension_points, extends):
        """
        Register a plugin with in features, singletons and extension points.
        This method should not be handled directly, use 'register_plugin'
        instead.
        
        @param features: the features this plugin is associated with.
        
        @param singletons: a list of singletons this plugin is registred to.
        
        @param extension_points: a list of a tuple of two elements: the name
        of the extension point and the extension points defined on that
        extension point.
        
        @param extends: a list of a tuple of two elements: the name of an
        extension point and the extension it should be registred.
        """
        # Check for singletons conflicts
        # In this case we do not allow overriding an existing Singleton
        for key in singletons:
            try:
                val = self.singletons[key]
                raise SingletonError(key)
            except KeyError:
                pass
    
        for key in singletons:
            self.singletons[key] = plugin
        
        for feat in features:
            self.features.add(feat, plugin)
        
        # initialize all the extensions in each extension point
        for holder_id, points in extension_points:
            self.ext_points[holder_id].init_extensions(points)
        
        extension_points = [name for name, points in extension_points]
        
        for holder_id, extension_point in extends:
            self.ext_points[holder_id].add(extension_point, plugin)
        
        
        self.plugins[plugin] = PluginEntry(plugin, features, singletons,
                                           extension_points, extends)
        
        return plugin
    
    def get_plugin_from_singleton(self, singleton):
        """Returns the plugin associated with this singleton."""
        try:
            return self.singletons[singleton]
        except KeyError:
            raise SingletonError(singleton)
    
    def unregister(self, plugin):
        """Removes a plugin from the registry."""
        entry = self.plugins[plugin]
        
        for key in entry.singletons:
            del self.singletons[key]
            
        for feat in entry.features:
            self.features.remove(feat, plugin)
            
        for holder_id in entry.extension_points:
            del self.ext_points[holder_id]
        
        for holder_id, ext_pnt in entry.extends.iteritems():
            self.ext_points[holder_id].remove(ext_pnt, plugin)

        del self.plugins[plugin]
        
        plugin.unplug(self)
    
    def register_plugin(self, *args, **kwargs):
        """Register a new plugin."""
        return self.register(*self.plugin_factory(*args, **kwargs))

    def get_features(self, feature, *args, **kwargs):
        for feature in self.features[feature]:
            yield feature.get_instance(self, *args, **kwargs)
    
    
    def get_singleton(self, singleton, *args, **kwargs):
        return self.get_plugin_from_singleton(singleton).get_instance(self, *args, **kwargs)
    
    def get_extension_point(self, holder_id, extension_point):
        return self.ext_points[holder_id].get_extension_point(extension_point)
    
    def get_extension_point_def(self, holder_id):
        return self.ext_points[holder_id].keys()
    
    def _check_plugin(self, plugin):
        entry = self.plugins[plugin]
        if len(entry.features) == 0 and len(entry.singletons) == 0:
            self.unregister(plugin)
    
    def unregister_singleton(self, singleton):
        try:
            plugin = self.singletons.pop(singleton)
            entry = self.plugins[plugin]
            entry.singletons.remove(singleton)
            self._check_plugin(plugin)

        except KeyError:
            raise SingletonError(singleton)
    
    def unregister_feature(self, feature, plugin):
        """
        In order to remove a feature u must have the associated plugin.
        """
        self.features.remove(feature, plugin)
        
        entry = self.plugins[plugin]
        entry.features.remove(feature)
        self._check_plugin(plugin)

    def __iter__(self):
        return iter(self.plugins)

    def clear(self):
        self.services = {}
        self.features.clear()
        for plugin in self.plugins:
            plugin.singeltons = []
            plugin.features = []
            plugin.unplug(self)
        self.plugins.clear()

