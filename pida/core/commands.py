# -*- coding: utf-8 -*-
"""
    Commandsconfig
    ~~~~~~~~~~~~~~

    They expose the commands a service/plugin provides via methods.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""
from pida.core.base import BaseConfig


class CommandsConfig(BaseConfig):

    def __call__(self, name, **kw):
        cmd = getattr(self, name)
        val = cmd(**kw)
        return val



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
