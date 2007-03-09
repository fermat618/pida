
from unittest import TestCase

from pida.core.service import Service, OptionsConfig, IOptions

class MYOptions(OptionsConfig):

    def create_options(self):
        self.svc.o_test = self.create_option(
            name='g1',
            label='G1 Label',
            rtype=None,
            default='default value',
            doc='Document for my group'
        )

class MYService(Service):
    
    options_config = MYOptions

class TestOptions(TestCase):

    def setUp(self):
        pass

    def test_options_setup(self):
        svc = MYService(boss=None)
        self.assertEqual(
            svc.reg.get_singleton(IOptions).get_option('g1'),
            svc.o_test
        )

    def test_option_get(self):
        svc = MYService(boss=None)
        self.assertEqual(
            svc.get_option('g1'), svc.o_test
        )

    def test_option_get_value(self):
        svc = MYService(boss=None)
        self.assertEqual(
            svc.opt('g1'), 'default value'
        )
        
