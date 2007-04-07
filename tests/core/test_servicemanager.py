

from unittest import TestCase
from tempfile import mkdtemp
import shutil
import os

from pida.core.interfaces import IService
from pida.core.servicemanager import ServiceLoader, ServiceManager

from pida.utils.testing.mock import Mock

from pida.core.environment import get_glade_path

class ServiceLoadTest(TestCase):

    def setUp(self):
        # A working service
        self._tdir = mkdtemp()
        self._spath = os.path.join(self._tdir, 'testservice')
        os.mkdir(self._spath)
        for name in ['__init__.py', 'testservice.py', 'service.pida']:
            f = open(os.path.join(self._spath, name), 'w')
            if name == 'testservice.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        self._spath = os.path.join(self._tdir, 'testservice2')
        os.mkdir(self._spath)
        for name in ['__init__.py', 'testservice2.py', 'service.pida']:
            f = open(os.path.join(self._spath, name), 'w')
            if name == 'testservice2.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        self._tdir2 = mkdtemp()
        self._spath2 = os.path.join(self._tdir2, 'testservice')
        os.mkdir(self._spath2)
        for name in ['__init__.py', 'testservice.py', 'service.pida']:
            f = open(os.path.join(self._spath2, name), 'w')
            if name == 'testservice.py':
                f.write('class NoService(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        self._tdir3 = mkdtemp()
        self._spath3 = os.path.join(self._tdir3, 'testservice')
        os.mkdir(self._spath3)
        for name in ['__init__.py', 'testservice.py']:
            f = open(os.path.join(self._spath3, name), 'w')
            if name == 'testservice.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        self._tdir4 = mkdtemp()
        self._spath4 = os.path.join(self._tdir4, 'nottestservice')
        os.mkdir(self._spath4)
        for name in ['__init__.py', 'testservice.py', 'service.pida']:
            f = open(os.path.join(self._spath4, name), 'w')
            if name == 'testservice.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        self._tdir5 = mkdtemp()
        self._spath5 = os.path.join(self._tdir5, 'testservice')
        os.mkdir(self._spath5)
        for name in ['__init__.py', 'testservice.py', 'service.pida']:
            f = open(os.path.join(self._spath5, name), 'w')
            if name == 'testservice.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()
        self._gladedir = os.path.join(self._spath5, 'glade')
        os.mkdir(self._gladedir)
        self._dumglade = os.path.join(self._gladedir, 'banana.glade')
        f = open(self._dumglade, 'w')
        f.close()
        self.loader = ServiceLoader()

    def test_get(self):
        services = [svc for svc in self.loader.get_all_services([self._tdir])]
        self.assertEqual(services[0].__name__, 'Service')

    def test_get_both(self):
        services = [svc for svc in self.loader.get_all_services([self._tdir])]
        self.assertEqual(len(services), 2)
        
    def test_load(self):
        services = [svc for svc in self.loader.load_all_services([self._tdir], None)]
        self.assertEqual(services[0].__class__.__name__, 'Service')

    def test_bad_load(self):
        services = [svc for svc in self.loader.get_all_services([self._tdir2])]
        self.assertEqual(services, [])

    def test_no_pidafile(self):
        services = [svc for svc in self.loader.get_all_services([self._tdir3])]
        self.assertEqual(services, [])

    def test_import_error(self):
        services = [svc for svc in self.loader.get_all_services([self._tdir4])]
        self.assertEqual(services, [])

    def test_env(self):
        self.loader.load_all_services([self._tdir5], None)
        gp = get_glade_path('banana.glade')
        self.assertEqual(gp, self._dumglade)

    def tearDown(self):
        shutil.rmtree(self._tdir)
        shutil.rmtree(self._tdir2)
        shutil.rmtree(self._tdir3)
        shutil.rmtree(self._tdir4)


class ServiceManagerTest(TestCase):

    def setUp(self):
        # A working service
        self._tdir = mkdtemp()
        self._spath = os.path.join(self._tdir, 'testservice')
        os.mkdir(self._spath)
        for name in ['__init__.py', 'testservice.py', 'service.pida']:
            f = open(os.path.join(self._spath, name), 'w')
            if name == 'testservice.py':
                f.write('class Service(object):\n')
                f.write('    def __init__(self, boss):\n')
                f.write('        """A test"""\n')
            f.close()

        class MyService:
            servicename = 'MyService'

        self._svc = MyService()

        self._boss = Mock(
            dict(
                get_service_dirs = [self._tdir]
            )
        )
        self._sm = ServiceManager(self._boss)


    def tearDown(self):
        shutil.rmtree(self._tdir)

    def test_service_manager_register(self):
        self._sm.register_service(self._svc)
        self.assertEqual(
            self._sm.get_service('MyService').servicename,
            self._svc.servicename
        )
        self.assertEqual(
            [s for s in self._sm.get_services()][0],
            self._svc
        )

    def test_service_manager_load(self):
        self._sm.load_services()
        self.assertEqual(
            self._sm.get_service('testservice').__class__.__name__,
            'Service'
        )
        self.assertEqual(
            [s for s in self._sm.get_services()][0].__class__.__name__,
            'Service'
        )

