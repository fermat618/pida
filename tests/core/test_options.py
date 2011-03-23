import pytest
from mock import Mock
from pida.core.options import OptionsConfig

@pytest.mark.xfail(reason='removed', run=False)
def test_extra(tmpdir):
    mock = Mock()
    mock.started = False
    opt = OptionsConfig(mock)
    opt.SUPPORTS_MULTIPLE_CONNECTIONS = True
    opt.register_extra_option(
                    name='test',
                    default=['default'],
                    callback=mock,
                    safe=True,
                    workspace=False,
                    path=tmpdir.join('opt.json'))
    assert not tmpdir.join('opt.json').check()
    assert opt.get_extra_value('test') == ['default']
    opt.set_extra_value('test', [2])
    # service is not started yet, so the callback didn't get fired
    assert not mock.called
    mock.started = True
    # not we test the real stuff
    opt.set_extra_value('test', [2])
    opt.save_extra('test')
    assert tmpdir.join('opt.json').check()
    assert mock.called
    assert not opt.get_extra_option('test').dirty
    opt.get_extra_option('test').dirty = True
    assert opt.get_extra_value('test') ==  [2]


