import py
from unittest import TestCase

from pida.core.service import Service

from pida.core.options import OptionsConfig
from pida.core.commands import CommandsConfig

from pida.core.log import log


class MockBoss(object):

    log = log

    def add_action_group_and_ui(*args):
        pass

    def remove_action_group_and_ui(*args):
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


def pytest_funcarg__svc(request):
    svc = MYService(boss=MockBoss())
    svc.create_all()
    request.addfinalizer(svc.destroy)
    return svc

def test_options_setup(svc):
    opt = svc.options.get_option('g1')
    assert opt == svc.o_test

def test_option_get(svc):
    assert svc.get_option('g1') == svc.o_test

def test_option_get_value(svc):
    assert svc.opt('g1') == 'default value'

def test_call_cmd(svc):
    assert not svc.something
    svc.cmd('do_something', val=True)
    assert svc.something

def test_passing_non_named_args_to_cmd(svc):
    py.test.raises(TypeError, svc.cmd, 'do_something', True)


@py.test.mark.xfail(run=False, reason="killed much of dbus")
def test_dbus_double_register(svc):
    svc2 = MYService(boss=MockBoss())
    # we can't start two services with the same name
    try:
        py.test.raises(KeyError, svc2.create_all)
    finally:
        svc2.destroy()


