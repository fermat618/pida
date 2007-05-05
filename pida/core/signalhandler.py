
import signal

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

class PosixSignalHandler(object):

    def __init__(self, boss):
        self.boss = boss
        signal.signal(signal.SIGTERM, self.handle_SIGTERM)

    def handle_SIGTERM(self, signum, frame):
        self.boss.log.error(_('PIDA stopped by SIGTERM')) 
        self.boss.stop(force=True)

