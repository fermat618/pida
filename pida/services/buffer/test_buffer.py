from pida.services.buffer.buffer import Buffer, BufferOptionsConfig
from pida.utils.testing.mock import Mock

def test_recover_loading_error():
    boss = Mock()
    svc = Buffer(boss)
    svc._documents = {}

    error = Mock()
    error.document = None
    error.message = 'test'
    #XXX: log messsages?
    svc.recover_loading_error(error)
    
def test_open_files_storage():
    svc = Mock()
    svc.get_name.return_value = 'test'
    options = BufferOptionsConfig(svc)
    options.create_options()
    
    #XXX too stupid
    assert options.get_option('open_files').workspace
