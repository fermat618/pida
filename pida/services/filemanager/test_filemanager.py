from pida.core.boss import Boss
from pida.utils.testing.mock import Mock
from pygtkhelpers.utils import refresh_gui
from .filemanager import FilemanagerView, Filemanager

def pytest_funcarg__view(request):
    #XXXX: factor services/mock services into a general conftest
    tmpdir = request.getfuncargvalue('tmpdir')
    browse = tmpdir.ensure('browse', dir=1)
    browse.ensure('test.py')
    boss = Mock(Boss)
    boss.cmd.return_value = []
    svc = Filemanager(boss)
    #XXX: evil
    svc.create_all()
    svc.subscribe_all()
    svc.pre_start()
    svc.start()
    svc.started = 1 
    svc.browse(str(browse))
    request.addfinalizer(svc.stop_components)
    return svc.file_view

def test_file_list_go_up(view, tmpdir):
    print list(view.file_list)
    assert len(view.file_list) == 1
    view.svc.go_up()
    assert view.path == tmpdir
    assert len(view.file_list) == 1

def test_file_list_doubl_click_parent_dir(view, tmpdir):
    pass #XXX: implement later


def test_delete_file(view, tmpdir, monkeypatch):
    monkeypatch.setattr(view.svc, 'yesno_dlg', lambda v:True)
    assert tmpdir.join('browse/test.py').check()
    view.file_list.selected_item = view.file_list[0]
    view.svc.actions.on_delete(None)
    refresh_gui()
    assert not tmpdir.join('browse/test.py').check()



