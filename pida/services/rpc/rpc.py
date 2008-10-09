# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# PIDA Imports
from pida.core.service import Service
from pida.utils.grpc import LocalServerDispatcher

class PidaDispatcher(LocalServerDispatcher):

    def __init__(self, svc):
        self.svc = svc
        LocalServerDispatcher.__init__(self, 9124)

    def remote_open(self, file_name):
        self.svc.boss.cmd('buffer', 'open_file', file_name=file_name)

# Service class
class Rpc(Service):
    """Describe your Service Here""" 

    def start(self):
        self._dispatcher = PidaDispatcher(self)

# Required Service attribute for service loading
Service = Rpc



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
