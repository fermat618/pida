# licence gpl2 or later
#XXX: this code is ugly like hell
import os
import sys
import StringIO
import urllib2
import base64
import hashlib

from optparse import OptionParser

from . import metadata
from . import packer
from . import multipart


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
        'summary': 'Pida Plugin: ' + meta.name,
        'description': meta.description,
        'version': meta.version,
        #XXX: extend
    }

def upload_plugin(base, plugin):
    meta = metadata.from_plugin(base, plugin)
    pack = packer.pack_plugin(base, plugin)
    io = StringIO.StringIO(pack)
    io.name = 'pida.plugins.%s-%s.zip' % (plugin, meta.version)

    data = extract_data(meta)
    data.update({
        # action
        ':action': 'file_upload',
        'protocol_version': '1',

        # content
        'content': io,
        'filetype': 'sdist', #XXX: ???
        'pyversion': '2.5', #XXX: argh
        'md5_digest': hashlib.md5(pack).hexdigest(),
    })

    do_request(data)

def upload_meta(base, plugin):
    meta = metadata.from_plugin(base, plugin)
    pack = meta.as_string(False)
    io = StringIO.StringIO(pack)
    io.name = 'pida.plugins.%s-%s.meta' % (plugin, meta.version)

    data = extract_data(meta)
    data.update({
        # action
        ':action': 'file_upload',
        'protocol_version': '1',

        # content
        'content': io,
        'filetype': 'sdist', #XXX: ???
        'pyversion': '2.5', #XXX: argh
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



def main():
    #XXX: config support
    parser = OptionParser()
    parser.add_option('-r', '--repository', dest='repo',)
    parser.add_option('-u', '--user', dest='user',)
    parser.add_option('-p', '--password', dest='pass',)

    options, args = parser.parse_args()

    actions = [
        ('register', register_plugin),
        ('meta', upload_meta),
        ('plugin', upload_plugin),
    ]

    for path in args:

        path = os.path.abspath(path)
        path = os.path.normpath(path)
        if not os.path.exists(os.path.join(path, 'service.pida')):
            continue
        base = os.path.dirname(path)

        plugin = os.path.basename(path)
        meta = metadata.from_plugin(base, plugin)
        print plugin,':', meta.name
        for action, method in actions:
            try:
                print plugin, '->', action,
                method(base, plugin)
                print 'works'
            except Exception, e:
                print 'fail', e
                import traceback
                traceback.print_exc()

