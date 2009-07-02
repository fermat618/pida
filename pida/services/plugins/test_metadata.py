

from .test_packer import skeleton_path
from .metadata import from_plugin, from_dict

def test_metadata_from_plugin():
    data = from_plugin(skeleton_path, 'skeleton')
    assert not data.is_new
    assert data.plugin == 'skeleton'
    assert data.name == '{{name}}'
    

def test_metadata_from_dict():
    data = from_dict(
            name='abc',
            plugin='foo',
            base='',
    )
    assert data.is_new
    assert data['Name'] == 'abc'



