# license gpl2 or later

import re
import urllib2
from . import metadata
from urllib import basejoin
import logging
log = logging.getLogger('pida.services.plugins.downloader')
#XXX: ugly hack to avout dealing with html trees
link_re = re.compile(r'''href=['"](.*?)["'].*?>(.*?)</''', re.M)
plugin_name_re = re.compile("""
    .* # prefix crud
    pida.plugins.(?P<name>\w+)-(?P<version>[\w.]+)
    .(?P<ext>zip|meta|egg|tar.bz|tar.gz)
    (?P<crud>.*)
""", re.VERBOSE)


def find_latest_metadata(url):
    for name, version, data in find_latest(url):
        if 'meta' not in data:
            log.error('%s-%s doesnt supply metadata', name, version)
            continue
        if 'tar.gz' not in data:
            log.error('%s-%s doesnt supply a packed plugin', name, version)
            continue
        plugin = name.split('.')[-1]
        try:
            fd = urllib2.urlopen(data['meta'])
        except urllib2.HTTPError:
            continue
        meta = metadata.from_string(fd.read(), None, plugin)
        meta.url = data['tar.gz']
        yield meta

def find_latest(url):
    for name, versions in find_plugin_versions(url):
        #XXX: better version key
        if not versions:
            continue
        latest = max(versions,key=lambda x:x.split('.'))
        yield name, latest, versions[latest]

def find_plugin_versions(url):
    for href, name in find_plugins(url):
        yield name, find_versions(basejoin(url, href))

def find_versions(url):
    versions = {}
    for href, name in find_urls(url):
        match = plugin_name_re.match(href)
        if match:
            version = match.group('version')
            ext = match.group('ext')
            if version not in versions:
                versions[version] = {}
            #XXX: might break for absolute url's
            versions[version][ext] = basejoin(url, href)
    return versions


def find_plugins(url):
    items = find_urls(url)
    return [
        (href, name)
        for href, name in items
        if 'pida' in href.lower()
     ]

def find_urls(url,):
    try:
        fd = urllib2.urlopen(url)
    except urllib2.URLError, e:
        log.warning("Can't contact plugin website")
        return ()
    data = fd.read()
    return link_re.findall(data)
