# license GPL 2 or later
# copyrtight 2009 by the pida team
# see COPYING

from .packer import find_files, pack_plugin
from os import path
from StringIO import StringIO
from tarfile import TarFile

skeleton_path = path.join(
    path.dirname(__file__),
    '..','..', '..', 
    'tools'
)




def test_find_files():
    files = find_files(skeleton_path, 'skeleton')
    assert files[0] == 'skeleton'
    assert path.basename(files[1]) == 'service.pida'
    assert len(files) == 7, 'the project skeleton has 7 items'

def test_pack_plugin():
    data = pack_plugin(skeleton_path, 'skeleton')
    files = find_files(skeleton_path, 'skeleton')

    io = StringIO(data)
    tarfile = TarFile.gzopen(None,fileobj=io)

    tar_files = [info.name for info in tarfile]
    
    for norm, tar in zip(files, tar_files):
        tar = path.normpath(tar)
        assert norm == tar


