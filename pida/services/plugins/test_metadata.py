

from .test_packer import skeleton_path
from .metadata import from_plugin, from_dict, is_plugin

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



def test_is_plugin(tmpdir):
    file = tmpdir.ensure('service/service.pida')
    file.write('a') # how mime messages usually could start
    assert is_plugin(str(tmpdir), 'service')

    file.write('[') # how the 0.5 plugins did start
    assert not is_plugin(str(tmpdir), 'service')


