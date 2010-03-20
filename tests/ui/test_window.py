
from pida.utils.testing import refresh_gui
from pida.utils.testing.mock import Mock
from pida.ui.window import PidaWindow
from pida.core.boss import Boss
from pida.services.window.window import Window as WindowSvc

def pytest_funcarg__boss(request):
    boss = Mock(Boss)
    boss.window = Mock(PidaWindow)
    boss.window.get_size.return_value = (640, 480)
    boss.window.get_position.return_value = (0, 0)
    boss.window.paned = Mock()
    boss.get_services.return_value = [] #XXX: mock up something for later
    return boss

def pytest_funcarg__svc(request):
    return Mock(WindowSvc)


def test_create(svc):
    win = PidaWindow(svc)
    refresh_gui()


def test_svc_setup(boss, monkeypatch, tmpdir):
    monkeypatch.setattr(WindowSvc, 'state_config',
                                str(tmpdir.join('really/missing.json')))
    svc = WindowSvc(boss)
    svc.started = 1
    svc.restore_state(pre=True)

    svc.save_state()



