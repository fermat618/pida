# license GPL 2 or later
# copyrtight 2009 by the pida team
# see COPYING

from .packer import find_files, pack_plugin, upload_plugin
from os import path
from StringIO import StringIO
from tarfile import TarFile

pida_plugins = path.join(
    path.dirname(__file__),
    '..','..', '..', 
    'pida-plugins'
)




def test_find_files():
    files = find_files(pida_plugins, 'skeleton')
    assert files[0] == 'skeleton'
    assert path.basename(files[1]) == 'service.pida'
    assert len(files) == 7, 'the project skeleton has 7 items'

def test_pack_plugin():
    data = pack_plugin(pida_plugins, 'skeleton')
    files = find_files(pida_plugins, 'skeleton')

    io = StringIO(data)
    tarfile = TarFile.gzopen(None,fileobj=io)

    tar_files = [info.name for info in tarfile]
    
    for norm, tar in zip(files, tar_files):
        tar = path.normpath(tar)
        assert norm == tar


