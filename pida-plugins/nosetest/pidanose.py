#!/usr/bin/env python
import sys, os

import nose
from nose.core import TestProgram
from nose.config import Config, all_config_files
from nose.plugins import Plugin
from nose.plugins.manager import PluginManager, DefaultPluginManager, \
     RestrictedPluginManager
import traceback
### configure paths, etc here
import dbus

class DBusReport(Plugin):

    name = 'dbus-reporter'
    score = 2 # run late

    def __init__(self):
        super(DBusReport, self).__init__()
        bus = dbus.SessionBus()
        object = bus.get_object(
            'uk.co.pida.pida.'+os.environ['PIDA_DBUS_UUID'],
            '/uk/co/pida/pida/nosetest'
            )
        self.proxy = dbus.Interface(object, 'uk.co.pida.pida.nosetest')
        self.proxy.beginProcess(os.getcwd())


    def addSuccess(self, test):
        description = test.shortDescription() or str(test)
        self.proxy.addSuccess(description)

    def addError(self, test, err):
        err = self.formatErr(err)
        description = test.shortDescription() or str(test)
        self.proxy.addError(description, err)

    def addFailure(self, test, err):
        err = self.formatErr(err)
        description = test.shortDescription() or str(test)
        self.proxy.addFailure(description, err)

    def finalize(self, result):
        self.proxy.endProcess()

    def formatErr(self, err):
        exctype, value, tb = err
        return ''.join(traceback.format_exception(exctype, value, tb))

    def startContext(self, ctx):
        try:
            n = ctx.__name__
        except AttributeError:
            n = str(ctx)
        try:
            path = ctx.__file__.replace('.pyc', '.py')
        except AttributeError:
            path = ''
        self.proxy.startContext(n, path)

    def stopContext(self, ctx):
        self.proxy.stopContext()

    def startTest(self, test):
        description = test.shortDescription() or str(test)
        self.proxy.startTest(description)

    def stopTest(self, test):
        self.proxy.stopTest()


class PidaTest(TestProgram):
    def makeConfig(self, env, plugins=None):
        """Load a Config, pre-filled with user config files if any are
        found.
        """
        cfg_files = all_config_files()
        if plugins:
            manager = PluginManager(plugins=plugins)
        else:
            manager = DefaultPluginManager()
        manager.addPlugin(DBusReport())
        return Config(
            env=env, files=cfg_files, plugins=manager)

sys.exit(PidaTest().sucess)

### do other stuff here
