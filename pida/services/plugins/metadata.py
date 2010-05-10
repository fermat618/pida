"""
    Pida plugin metadata
    ~~~~~~~~~~~~~~~~~~~~


    :license: GPL2 or later
    :copyright: 2009 by the pida team

"""
from __future__ import with_statement

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
    
    def __repr__(self):
        return '<Plugin metadata %s: %s>'%(getattr(self, 'plugin', None), self.name)


    @property
    def markup(self):
        if self.is_new:
            return '<span color="red"><b>!N</b></span> %s' % self.name
        return self.name


def from_plugin(base, plugin, enabled=False):
    #XXX: pkgutil/pkg_resources ?
    path = os.path.join(base, plugin, 'service.pida')

    with open(path) as f:
        return from_string(f.read(), base, plugin, enabled)


def from_string(data, base, plugin, enabled=False):
    parser = FeedParser(PluginMessage)
    parser.feed(data)
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
        f.write(meta.as_string(False))

def is_plugin(base, plugin):
    p = os.path.join(base, plugin, 'service.pida')
    if os.path.exists(p):
        with open(p) as f:
            return f.read(1) != '[' # pida 0.5
