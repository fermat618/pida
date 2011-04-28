

from pida.core import boss
from mock import Mock

def test_firstrun(monkeypatch):
    from pida.utils import firstrun
    mock = Mock()
    mock().run.return_value = None, None
    monkeypatch.setattr(firstrun, 'FirstTimeWindow', mock)
    boss.Boss()

