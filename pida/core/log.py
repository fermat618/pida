# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.log
    ~~~~~~~~~~~~~

    sets up the core logging

    :copyright: 2007 the Pida Project
    :license: GPL2 or later
"""


import logging
import logging.handlers

from logging import getLogger as get_logger

from pida.core.environment import is_debug
from pida.utils.descriptors import cached_property

format_str = '%(levelname)s %(name)s: %(message)s'
format = logging.Formatter(format_str)

log = get_logger('pida')
handler = logging.StreamHandler()
handler.setFormatter(format)
log.addHandler(handler)

def setup():
    if is_debug():
        get_logger().setLevel(logging.DEBUG)
    else:
        get_logger().setLevel(logging.INFO)

class Log(object):

    def get_name(self):
        return '%s.%s' % (self.__module__, self.__class__.__name__)

    @cached_property
    def log(self):
        return get_logger(self.get_name())

