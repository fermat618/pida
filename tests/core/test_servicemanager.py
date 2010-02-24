

from unittest import TestCase
from tempfile import mkdtemp
import imp
import os
import shutil
import sys

from os.path import join

from pida.core.servicemanager import ServiceLoader, ServiceManager

#XXX: replace with something better
from pida.core.environment import get_resource_path

test_service = '''
from pida.core.service import Service as BaseService
class TestService(BaseService):
    pass
Service = TestService
'''

class PseudoPackage(object):
    base = imp.new_module('pida_oblivious_test')

    """very hacky thing to get service"""
    def __init__(self, name):
        self.name = name
        self.mod = imp.new_module('pida_oblivious_test.' + name)
        self.mod.__self__ = self
        self.path = join(mkdtemp(), name)

        os.mkdir(self.path)
        open(join(self.path, '__init__.py'), 'w').close()
        self.mod.__path__ = [self.path]
        self.loader = ServiceLoader(self.mod)

        sys.modules[self.base.__name__] = self.base
        sys.modules[self.mod.__name__] = self.mod
        setattr(self.base, name, self.mod)

    def gen_files(self, sname, *names, **kw):
        content = kw.get('content', '')
        for name in names:
            f = open(join(self.path, sname, name), 'w')
            try:
                f.write(content)
            finally:
                f.close()

    def gen_service(self, name, service=test_service, altname=None):
        spath = join(self.path, name)
        os.mkdir(spath)
        self.gen_files(name, '__init__.py', 'service.pida')
        self.gen_files(name, altname or name + '.py', content=service)
        return spath

    def clean(self):
        del sys.modules[self.mod.__name__]
        delattr(self.base, self.name)
        shutil.rmtree(self.path)

def gen(self, *k, **kw):
    return self.gen_service(*k, **kw)

class ServiceLoadTest(TestCase):

    def setUp(self):
        # A working service
        self.p1 = p1 = PseudoPackage('t1')
        gen(p1, 'testservice')
        gen(p1, 'testservice2')

        self.p2 = p2 = PseudoPackage('t2')
        gen(p2, 'testservice2',
            service=(
                'class NoService(object):\n'
                '    def __init__(self, boss):\n'
                '        """A test"""\n'
                ))
        self.p3 = p3 = PseudoPackage('t3')
        e = gen(p3, 'testservice')
        os.unlink(join(e, 'service.pida'))  # dont load on missing service file

        self.p4 = p4 = PseudoPackage('t4')
        gen(p4, 'nottestservice', altname='testservice.py')

        self.p5 = p5 = PseudoPackage('t5')
        self._spath5 = gen(p5, 'testservice')
        self._gladedir = os.path.join(self._spath5, 'glade')
        os.mkdir(self._gladedir)
        self._dumglade = os.path.join(self._gladedir, 'banana.glade')
        f = open(self._dumglade, 'w')
        f.close()

        self.l1 = p1.loader
        self.l2 = p2.loader
        self.l3 = p3.loader
        self.l4 = p4.loader
        self.l5 = p5.loader

    def test_get(self):
        services = self.l1.get_all()
        self.assertEqual(services[0].__name__, 'TestService')

    def test_get_both(self):
        services = self.l1.get_all()
        self.assertEqual(len(services), 2)

    def test_bad_load(self):
        services = self.l2.get_all()
        self.assertEqual(services, [])

    def test_no_pidafile(self):
        services = self.l3.get_all()
        self.assertEqual(services, [])

    def test_import_error(self):
        services = self.l4.get_all()
        self.assertEqual(services, [])

    def __borked__test_env(self):
        self.loader.load_all_services([self._tdir5], None)
        gp = get_resource_path('glade', 'banana.glade')
        self.assertEqual(gp, self._dumglade)

    def tearDown(self):
        self.p1.clean()


class ServiceManagerTest(TestCase):

    def setUp(self):
        # A working service
        self.p = p = PseudoPackage('m1')
        gen(p, 'testservice')
        class MyService:
            @staticmethod
            def get_name():
                return 'MyService'

        self.svc = MyService()

        self.sm = ServiceManager(None)
        #XXX internal hack
        self.sm._loader = p.loader

    def tearDown(self):
        self.p.clean()

    #FIXME
    def __borked__test_service_manager_register(self):
        service = self.sm._loader.get_one('testservice')
        self.sm._register(service)
        self.assertEqual(
            self.sm.get_service('myservice').get_name(),
            self.svc.get_name()
        )
        self.assertEqual(
            self.sm.get_services()[0],
            self._svc
        )

    #FIXME
    def __borked__test_service_manager_load(self):
        self._sm._loader.get_all(self._spath)
        self.assertEqual(
            self._sm.get_service('testservice').__class__.__name__,
            'Service'
        )
        self.assertEqual(
            [s for s in self._sm.get_services()][0].__class__.__name__,
            'Service'
        )

