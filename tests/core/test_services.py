
from unittest import TestCase

from pida.core.service import Service

from pida.core.options import OptionsConfig
from pida.core.commands import CommandsConfig

from pida.core.interfaces import IOptions
from pida.core.log import log


class MockBoss(object):

    log = log

    def add_action_group_and_ui(*args):
        pass


class MYOptions(OptionsConfig):

    def create_options(self):
        self.svc.o_test = self.create_option(
            name='g1',
            label='G1 Label',
            type=str,
            default='default value',
            doc='Document for my group'
        )

class MyCommands(CommandsConfig):

    def do_something(self, val):
        self.svc.something = val

class MYService(Service):

    options_config = MYOptions
    commands_config = MyCommands

    def __init__(self, boss):
        Service.__init__(self, boss)
        self.something = False
        self.started = False

class TestOptions(TestCase):

    def setUp(self):
        pass

    def test_options_setup(self):
        svc = MYService(boss=MockBoss())
        svc.create_all()
        self.assertEqual(
            svc.options.get_option('g1'),
            svc.o_test
        )

    def test_option_get(self):
        svc = MYService(boss=MockBoss())
        svc.create_all()
        self.assertEqual(
            svc.get_option('g1'), svc.o_test
        )

    def test_option_get_value(self):
        svc = MYService(boss=MockBoss())
        svc.create_all()
        self.assertEqual(
            svc.opt('g1'), 'default value'
        )

class TestCommands(TestCase):

    def setUp(self):
        self.svc = MYService(boss=MockBoss())
        self.svc.create_all()

    def test_call(self):
        self.assertEqual(self.svc.something, False)
        self.svc.cmd('do_something', val=True)
        self.assertEqual(self.svc.something, True)

    def test_non_named(self):
        def c():
            self.svc.cmd('do_something', True)
        self.assertRaises(TypeError, c)




