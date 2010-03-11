from . import plugins

import py
from pida.utils.testing.mock import Mock

#XXX: larger unittests for the downloader?!

def pytest_funcarg__boss(request):
    return Mock()

def pytest_funcarg__svc(request):
    boss = request.getfuncargvalue('boss')
    mp = request.getfuncargvalue('monkeypatch')
    mo.setattr(plugins, 'ServiceLoader', lambda x: boss.sm)

    svc = plugins.Plugins(boss)
    return svc

class PP(object):
    '''Pseudo plugin for the enable/disable view'''
    def __init__(self, name, enabled):
        self.name = name
        self.plugin = name
        self.enabled = enabled


def test_plugins_view_enable_and_disable():
    svc = Mock()
    view = plugins.PluginsView(svc)

    foo = PP('foo', True)
    bar = PP('bar', False)
    view.installed_list.extend([foo, bar])

    svc.start_plugin.return_value = True

    view.on_installed_list__item_changed(None, foo, 'enabled', True)
    assert svc.start_plugin.called
    assert foo.enabled

    view.on_installed_list__item_changed(None, bar, 'enabled', False)
    assert svc.stop_plugin.called
