from unittest import TestCase
from pida.core.options import OptionsManager, OptionsConfig
from tempfile import mktemp
from .test_services import MockBoss
from pida.core.service import Service


o = OptionsManager(None)
boss = MockBoss()

class MYService(Service):

    options_config = OptionsConfig

    def __init__(self, boss):
        Service.__init__(self, boss)
        self.something = False
        self.started = False


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
        service = MYService(boss)
        service.create_all()
        #opt = OptionsConfig(service)
        opt = service.options
        opt.SUPPORTS_MULTIPLE_CONNECTIONS = True
        opt.register_extra_option('test', ['default'],
                      callback=self.extra_callback,
                      safe=True, workspace=False, path=self.path)
        self.assertEqual(opt.get_extra_value('test'), ['default'])
        opt.set_extra_value('test', [2])
        # service is not started yet, so the callback didn't get fired
        self.assertEqual(self.last_call, None)
        service.started = True
        # not we test the real stuff
        opt.set_extra_value('test', [2])
        self.assertEqual(opt.get_extra_value('test'), [2])
        self.assertEqual(self.last_call.value, [2])
        self.assertEqual(self.last_call.dirty, False)
        self.last_call.dirty = True
        self.assertEqual(opt.get_extra_value('test'), [2])
        service.destroy()

        #opt2 = OptionsConfig(service)

