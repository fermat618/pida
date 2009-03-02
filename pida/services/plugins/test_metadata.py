

from .test_packer import pida_plugins
from .metadata import from_plugin, from_dict

def test_metadata_from_plugin():
    data = from_plugin(pida_plugins, 'skeleton')
    print data.name
    assert not data.is_new
    assert data.plugin == 'skeleton'
    assert data.name == 'Skeleton'
    

def test_metadata_from_dict():
    data = from_dict(
            name='abc',
            plugin='foo',
            base='',
    )
    assert data.is_new
    assert data['Name'] == 'abc'



