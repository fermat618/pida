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

from collections import deque
from threading import Lock


log = logbook.Logger('pida')

def configure():
    if is_debug():
        pida_handler.level = logbook.DEBUG
    else:
        pida_handler.level = logbook.NOTICE

class Log(object):

    def get_name(self):
        return '%s.%s' % (self.__module__, self.__class__.__name__)

    @cached_property
    def log(self):
        return logbook.Logger(self.get_name())


class RollOverHandler(logbook.Handler):
    """
    massively dumbed down version of logbooks FingersCrossedHandler
    """
    #XXX: unittests
    def __init__(self, filter=None, bubble=False):
        logbook.Handler.__init__(self, logbook.NOTSET, filter, bubble)
        self.lock = Lock()
        self._handler = None
        self.buffered_records = deque()

    def close(self):
        if self._handler is not None:
            self._handler.close()

    def enqueue(self, record):
        assert self.buffered_records is not None, 'rollover occurred'
        self.buffered_records.append(record)

    def rollover(self, handler):
        assert self.buffered_records is not None, 'rollover occurred'
        with self.lock:
            self._handler = handler
            for old_record in self.buffered_records:
                self._handler.emit(old_record)
            self.buffered_records = None

    @property
    def triggered(self):
        """This attribute is `True` when the action was triggered.  From
        this point onwards the handler transparently
        forwards all log records to the inner handler.
        """
        return self._handler is not None

    def emit(self, record):
        with self.lock:
            if self._handler is not None:
                self._handler.emit(record)
            else:
                self.enqueue(record)




null = logbook.NullHandler()
pida_handler = logbook.StderrHandler()
rollover = RollOverHandler(bubble=True)

nested_setup = logbook.NestedSetup([ null, pida_handler, rollover ])
nested_setup.push_application()
