pytest_plugins = "unittest",



import py
from pida.utils.testing.mock import Mock

collect_ignore = ['tools/skeleton']

class PidaClassCollect(py.test.collect.Class):
    def collect(self):
        # ignore classes that want params
        if not hasattr(self.obj, '__init__'):
            return super(PidaClassCollect, self).collect()


class Module(py.test.collect.Module):
    Class = PidaClassCollect

    def makeitem(self, name, obj):
        if isinstance(obj, Mock):
            return
        return super(Module, self).makeitem(name, obj)
