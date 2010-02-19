# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    Event Configs
    ~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from base import SubscriberConfig

class EventsConfig(SubscriberConfig):

    foreign_name = 'events'

    def emit(self, event, **kw):
        for callback in self[event]:
            callback(**kw)

