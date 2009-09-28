pytest_plugins = "unittest",



import py
from pida.utils.testing.mock import Mock

collect_ignore = ['tools/skeleton']

class Module(py.test.collect.Module):

    def makeitem(self, name, obj):
        if isinstance(obj, Mock):
            return
        return super(Module, self).makeitem(name, obj)
