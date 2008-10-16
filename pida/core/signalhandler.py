# -*- coding: utf-8 -*-
"""
    Posix Signal Handlers
    ~~~~~~~~~~~~~~~~~~~~~

    This is a crude hack for propper exiting.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import signal

# locale
from pida.core.locale import Locale
from pida.core.log  import log
locale = Locale('pida')
_ = locale.gettext

def handle_signals(boss):

    def SIGTERM(self, signum, frame):
        log.error(_('PIDA stopped by SIGTERM')) 
        boss.stop(force=True)

    def SIGINT(self, signum, frame):
        log.info(_('PIDA stopped by SIGINT')) 
        boss.stop(force=True)

    signal.signal(signal.SIGTERM, SIGTERM)
    signal.signal(signal.SIGINT, SIGINT)
