import py
from pida.utils.testing.mock import Mock
from pida.ui.window import PidaWindow
editors = 'vim', 'emacs', 'mooedit'

def pytest_generate_tests(metafunc):
    if 'editor' in metafunc.funcargnames:
        for editor in editors:
            metafunc.addcall(id=editor, param=editor)

class MockConfig(object):
    def subscribe(self, point, *data):
        pass

class MockService(object):
    def __init__(self, name):
        self.name = name

    events = MockConfig()

class MockBoss(object):
    def __init__(self):
        self.window = PidaWindow(self)
        self.window.start()

    def add_action_group_and_ui(self, actions, ui):
        pass

    remove_action_group_and_ui = add_action_group_and_ui

    def get_service(self, service):
        return MockService(service)
    
    window = Mock()

def pytest_funcarg__editor(request):
    e = request.param, request.param
    module = __import__('pida.editors.%s.%s'%e, fromlist=['*'])
    e = module.Service.get_sanity_errors()
    #XXX: py.test stdio redirection will break vim version guessing
    if (request.param != 'vim') and e:
        py.test.skip(e)
    boss = MockBoss()
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

