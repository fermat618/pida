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
from email import message_from_file

class _hd(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, object, owner):
        if object is None:
            return self
        return object.get(self.name)


class PluginMessage(Message):
    name = _hd('Name')
    author = _hd('Author')
    version = _hd('Version')
    depends = _hd('Depends')
    category = _hd('Category') #XXX list ?
    url = _hd('Location')
    description = property(Message.get_payload, Message.set_payload)

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

