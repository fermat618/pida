
import signal

class PosixSignalHandler(object):

    def __init__(self, app):
        self._app = app
        signal.signal(signal.SIGTERM, self.handle_SIGTERM)

    def handle_SIGTERM(self, signum):
        self.log.error('PIDA stopped by SIGTERM') 
        self._app.boss.stop()

