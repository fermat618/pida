from . import metadata
from . import packer
from . import multipart
import StringIO
import urllib2
import base64
import hashlib



def do_request(data):
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, 'localhost:8080', 'ronny', 'test')

    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler, multipart.MultipartPostHandler)

    req = urllib2.Request('http://localhost:8080/', data)
    res = opener.open(req)
    return res


def extract_data(meta):
    return {
        # infos
        'name': 'pida.plugins.'+ meta.plugin, #XXX?!
        'description': meta.name,
        'long_description': meta.description,
        'version': meta.version,
        #XXX: extend
    }


def upload_plugin(base, plugin):
    meta = metadata.from_plugin(base, plugin)
    pack = packer.pack_plugin(base, plugin)
    io = StringIO.StringIO(pack)
    io.name = 'pida-plugin-%s-%s.zip' % (plugin, meta.version)

    data = extract_data(meta)
    data.update({
        # action
        ':action': 'file_upload',
        'protocol_version': '1',

        # content
        'content': io,
        'filetype': 'sdist', #XXX: ???
        'pyversion': '2.5', #XXX:
        'md5_digest': hashlib.md5(pack).hexdigest(),
    })

    do_request(data)



def register_plugin(base, plugin):
    meta = metadata.from_plugin(base, plugin)
    data = extract_data(meta)

    data.update({
        ':action': 'submit',
        'metadata_version' : '1.0',
    })

    return do_request(data)

