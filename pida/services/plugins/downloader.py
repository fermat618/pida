# license gpl2 or later

import re
import urllib2
from xml.etree import ElementTree
from . import metadata
from urllib import basejoin
from collections import defaultdict

url = 'http://localhost:8080/simple'
url = 'http://pypi.python.org/simple/'



#XXX: ugly hack to avout dealing with html trees
link_re = re.compile(r'''href=['"](.*?)["'].*?>(.*?)</''', re.M)
plugin_name_re = re.compile("""
    .* # prefix crud
    (?P<name>\w+)-(?P<version>[\w.]+)
    .(?P<ext>zip|meta|egg|tar.bz|tar.gz)
    (?P<crud>.*)
""", re.VERBOSE)

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
    return [(href, name) for href, name in items if 'pida' in href]

def find_urls(url,):
    fd = urllib2.urlopen(url)
    data = fd.read()
    return link_re.findall(data)
