
import os, sys

sys.path.insert(0, os.getcwd())

from pida.utils.grpc import LocalClientDispatcher

from pida.utils.testing import refresh_gui

class PidaClientDispatcher(LocalClientDispatcher):

    def remote_ok(self, command):
        pass

    def remote_error(self, command):
        print 'Error'

if __name__ == '__main__':
    dispatcher = PidaClientDispatcher(9124)
    file_name = os.path.abspath(sys.argv[-1])
    dispatcher.call_server('open', (file_name,))
    refresh_gui()
