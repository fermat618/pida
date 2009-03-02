

from .test_packer import pida_plugins
from .metadata import from_plugin

def test_read_meta():
    data = from_plugin(pida_plugins, 'skeleton')
    print data.name
    assert not data.is_new
    assert data.plugin == 'skeleton'
    assert data.name == 'Skeleton'
    


