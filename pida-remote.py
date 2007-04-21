#! /usr/bin/env python

import os, sys

from pida.utils.grpc import LocalClientDispatcher
from pida.utils.testing import refresh_gui

class PidaClientDispatcher(LocalClientDispatcher):

    def remote_ok(self, command):
        sys.exit(0)

def main():
    dispatcher = PidaClientDispatcher(9124)
    file_name = os.path.abspath(sys.argv[-1])
    dispatcher.call_server('open', (file_name,))
    refresh_gui()
    print 'Error: PIDA was not available'
    sys.exit(1)

if __name__ == '__main__':
    main()
