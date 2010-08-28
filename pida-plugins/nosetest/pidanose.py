#!/usr/bin/env python
from __future__ import print_function
import sys, os
import io

if __name__ == '__channelexec__':
    sys.stdout = io.BytesIO()
import nose
from nose.core import TestProgram
from nose.config import Config, all_config_files
from nose.plugins import Plugin
import traceback
### configure paths, etc here

def send(kind, test=None, err=None):
    if err:
        err = ''.join(traceback.format_exception(*err))
    if test:
        description = test.shortDescription() or str(test)
    else:
        description = None
    channel.send((kind, description, err))

class ChannelReporter(Plugin):
    name = 'execnet'
    @property
    def enabled(self):
        return True

    @enabled.setter
    def enabled(self, val):
        pass


    def addSuccess(self, test):
        send('success', test)

    def addError(self, test, err):
        send('error', test, err)

    def addFailure(self, test, err):
        send('failure', test, err)

    def startContext(self, ctx):
        try:
            n = ctx.__name__
        except AttributeError:
            n = str(ctx)
        try:
            path = ctx.__file__.replace('.pyc', '.py')
        except AttributeError:
            path = ''
        channel.send(('start_ctx', n, path))

    def stopContext(self, ctx):
        channel.send(('stop_ctx',))

    def startTest(self, test):
        send('start', test)

    def stopTest(self, test):
        send('stop')


if __name__ == '__channelexec__':
    cwd = channel.receive()
    os.chdir(cwd)
    prog = TestProgram(
        exit=False,
        argv=['--with-execnet'],
        plugins=[ChannelReporter()],
        )

