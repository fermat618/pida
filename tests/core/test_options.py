from unittest import TestCase
import os
from pida.core.options import OptionsManager, OptionsConfig
from pida.utils.testing.mock import Mock
from tempfile import mktemp
from .test_services import MYService, MockBoss

o = OptionsManager(None)
boss = MockBoss()
service = MYService(boss)
service.started = True

class OptionConfigTest(TestCase):
    def setUp(self):
        self.path = mktemp()
        self.last_call = None

    def tearDown(self):
        #os.unlink(self.path)
        pass

    def extra_callback(self, option):
        self.last_call = option

    def test_extra(self):
        opt = OptionsConfig(service)
        opt.SUPPORTS_MULTIPLE_CONNECTIONS = True
        opt.register_extra_file(self.path, ['default'], 
                      callback=self.extra_callback, 
                      safe=True, workspace=False)
        self.assertEqual(opt.get_extra(self.path), ['default'])
        opt.set_extra_value(self.path, [2])
        self.assertEqual(opt.get_extra(self.path), [2])
        self.assertEqual(self.last_call.value, [2])
        self.assertEqual(self.last_call.dirty, False)
        self.last_call.dirty = True
        self.assertEqual(opt.get_extra(self.path), [2])

        #opt2 = OptionsConfig(service)