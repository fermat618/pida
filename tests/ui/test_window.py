
from pida.utils.testing import refresh_gui
from pida.utils.testing.mock import Mock
from pida.ui.window import PidaWindow
from pida.core.boss import Boss
from pida.services.window.window import Window as WindowSvc

def pytest_funcarg__boss(request):
    return Mock(Boss)

def pytest_funcarg__svc(request):
    return Mock(WindowSvc)


def test_create(svc):
    win = PidaWindow(svc)
    refresh_gui()


def test_svc_setup(boss, monkeypatch, tmpdir):
    monkeypatch.setattr(WindowSvc, 'state_config',
                                str(tmpdir.join('missing.json')))
    svc = WindowSvc(boss)
    svc.restore_state(pre=True)


