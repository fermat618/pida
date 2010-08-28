from pida.services.buffer.buffer import Buffer
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
