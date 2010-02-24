from .optionsmanager import PidaOptionsView
from pida.utils.testing.mock import Mock

def test_instanciate_options_view():
    svc = Mock()
    svc.get_label.return_value = 'test'
    svc.boss.get_services.return_value=[svc]

    view = PidaOptionsView(svc)
    assert not view.options_book.props.show_tabs
