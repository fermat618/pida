import py
from pida.utils.testing.mock import Mock
from pida.core.boss import Boss
from pida.core.events import EventsConfig
from pida.ui.window import PidaWindow
editors = 'vim', 'emacs', 'mooedit'
#XXX: ronny cant really test the 2 others atm
editors = 'vim',

def pytest_generate_tests(metafunc):
    if 'editor' in metafunc.funcargnames:
        for editor in editors:
            metafunc.addcall(id=editor, param=editor)


def mock_service(name):
    self = Mock()
    self.name = name
    self.events = Mock(spec=EventsConfig)
    return self

def mock_boss():
    self = Mock(spec=Boss)
    self.window = PidaWindow(self)
    self.window.start()
    self.get_service.side_effect = mock_service
    return self


def pytest_funcarg__editor(request):
    e = request.param, request.param
    module = __import__('pida.editors.%s.%s' % e, fromlist=['*'])
    e = module.Service.get_sanity_errors()
    #XXX: py.test stdio redirection will break vim version guessing
    if (request.param != 'vim') and e:
        py.test.skip(e)
    boss = mock_boss()
    service = module.Service(boss)
    service.create_all()
    service.subscribe_all()
    service.pre_start()
    service.start()
    service.started = True

    def finalizer():
        service.stop()
        service.stop_components()
        service.boss.window.destroy()
    request.addfinalizer(finalizer)
    return service

