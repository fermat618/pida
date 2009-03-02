"""
    Pida plugin metadata
    ~~~~~~~~~~~~~~~~~~~~


    :license: GPL2 or later
    :copyright: 2009 by the pida team

"""
from __future__ import with_statement
from simplejson import loads
import urllib2

import os

from email.message import Message
from email.feedparser import FeedParser

class _hd(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, object, owner):
        if object is None:
            return self
        return object.get(self.name)

    def __set__(self, object, value):
        print self.name
        if self.name not in object:
            object[self.name] = value
        else:
            object.replace_header(self.name, value)

#XXX: 
class PluginMessage(Message, object):

    name = _hd('Name')
    author = _hd('Author')
    version = _hd('Version')
    depends = _hd('Depends')
    category = _hd('Category') #XXX list ?
    url = _hd('Location')
    description = property(
        Message.get_payload, 
        Message.set_payload)
    
    
    @property
    def markup(self):
        if self.isnew:
            return '<span color="red"><b>!N</b></span> %s' % self.name
        return self.name


def from_plugin(base, plugin, enabled=False):
    path = os.path.join(base, plugin, 'service.pida')
    parser = FeedParser(PluginMessage)

    with open(path) as f:
        parser.feed(f.read())
    message = parser.close()
    message.is_new = False
    message.enabled = enabled
    message.plugin = plugin
    message.base = base
    return message


def from_dict(**kw):
    message = PluginMessage()
    for k, v in kw.iteritems():
        setattr(message, k, v)
    message.is_new = True #XXX: sematics?
    message.base = None
    return message

def serialize(base, plugin, meta):
    path = os.path.join(base, plugin, 'service.pida')
    with open(path, 'w') as f:
        f.write(meta.to_string(True))

def fetch_plugins(publisher):
    data = urllib2.urlopen(publisher)
    plugins = loads(data)
    return map(from_dict, data)

def is_plugin(base, plugin):
    return path.exists(path.join(base, plugin, 'service.pida'))
