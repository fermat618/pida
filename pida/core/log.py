# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.log
    ~~~~~~~~~~~~~

    sets up the core logging

    :copyright: 2007 Ronny Pfannschmidt
    :license: GPL2 or later
"""


import os
import warnings
import logging
import logging.handlers

from logging import getLogger as get_logger

from pida.core.environment import opts

format_str = '%(levelname)s %(name)s: %(message)s'
format = logging.Formatter(format_str)

log = get_logger('pida')
handler = logging.StreamHandler()
handler.setFormatter(format)
log.addHandler(handler)


if opts.debug:
    get_logger().setLevel(logging.DEBUG)
else:
    get_logger().setLevel(logging.INFO)

