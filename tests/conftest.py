pytest_plugins = "unittest",



import py
from pida.utils.testing.mock import Mock


class PidaClassCollect(py.test.collect.Class):
    def collect(self):
        try:
            #XXX: kinda ignore classes that want params
            self.obj()
            return super(PidaClassCollect, self).collect()
        except:
            return []


class Module(py.test.collect.Module):
    Class = PidaClassCollect

    def makeitem(self, name, obj):
        if isinstance(obj, Mock):
            return
        return super(Module, self).makeitem(name, obj)
