# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.log
    ~~~~~~~~~~~~~

    sets up the core logging

    :copyright: 2007 the Pida Project
    :license: GPL2 or later
"""


import logbook.compat
logbook.compat.redirect_logging()

from pida.core.environment import is_debug
from pida.utils.descriptors import cached_property

#XXX: replace with logbook.logger later
from logging import getLogger as get_logger

log = get_logger('pida')

def setup():
    if is_debug():
        pida_handler.level = logbook.DEBUG
    else:
        pida_handler.level = logbook.NOTICE

class Log(object):

    def get_name(self):
        return '%s.%s' % (self.__module__, self.__class__.__name__)

    @cached_property
    def log(self):
        return get_logger(self.get_name())


class RollOverHandler(logbook.Handler):
    pass



null = logbook.NullHandler()
pida_handler = logbook.StderrHandler()
rollover = RollOverHandler(bubble=True)

nested_setup = logbook.NestedSetup([ null, pida_handler, rollover ])
nested_setup.push_application()
