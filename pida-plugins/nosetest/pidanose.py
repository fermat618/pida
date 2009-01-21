#!/usr/bin/env python
import sys

import nose
from nose.core import TestProgram
from nose.config import Config, all_config_files
from nose.plugins.manager import PluginManager, DefaultPluginManager, \
     RestrictedPluginManager
from xmlplugin.xmlplugin import XmlOutput
### configure paths, etc here

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
        manager.addPlugin(XmlOutput())
        return Config(
            env=env, files=cfg_files, plugins=manager)

sys.exit(PidaTest().sucess)

### do other stuff here
