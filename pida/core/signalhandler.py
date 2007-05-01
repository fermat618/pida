
import signal

class PosixSignalHandler(object):

    def __init__(self, boss):
        self.boss = boss
        signal.signal(signal.SIGTERM, self.handle_SIGTERM)

    def handle_SIGTERM(self, signum):
        self.boss.log.error('PIDA stopped by SIGTERM') 
        self.boss.stop()

