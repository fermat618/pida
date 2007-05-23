# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


# system import(s)
import os
import sys
import signal
import warnings

from pida.core.signalhandler import PosixSignalHandler

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

def die_cli(message, exception=None):
    """Die in a command line way."""
    print message
    if exception:
        print exception
    print _('Exiting. (this is fatal)')
    sys.exit(1)


# First gtk import, let's check it
try:
    import gtk
    from gtk import gdk
    gdk.threads_init()
    if gtk.pygtk_version < (2, 8):
        die_cli(_('PIDA requires PyGTK >= 2.8. It only found %(major)s.%(minor)s')
                % {'major':gtk.pygtk_version[:2][0], 'minor':gtk.pygtk_version[:2][1]})
except ImportError, e:
    die_cli(_('PIDA requires Python GTK bindings. They were not found.'), e)


try:
    from kiwi.ui.dialogs import error
    def die_gui(message, exception):
        """Die in a GUI way."""
        error(_('Fatal error, cannot start PIDA'), 
              long='%s\n%s' % (message, exception))
        die_cli(message)

except ImportError, e:
    die_cli(_('Kiwi needs to be installed to run PIDA'), e)


# Python 2.4
if sys.version_info < (2,4):
    die_gui(_('Python 2.4 is required to run PIDA. Only %(major)s.%(minor)s was found.') %
        {'major':sys.version_info[:2][0], 'minor':sys.version_info[:2][1]})


# This can test if PIDA is installed
try:
    from pida.core.environment import Environment
    from pida.core.boss import Boss
    from pida import PIDA_VERSION
except ImportError, e:
    die_gui(_('The pida package could not be found.'), e)


def run_version(env):
    print _('PIDA, version %s') % PIDA_VERSION
    return 0


def run_pida(env):
    b = Boss(env)
    PosixSignalHandler(b)
    b.start()
    gdk.threads_enter()
    b.loop_ui()
    gdk.threads_leave()
    return 0

def force_quit(signum, frame):
    os.kill(os.getpid(), 9)

# Set the signal handler and a 5-second alarm

def set_trace():
    import linecache
    def traceit(frame, event, arg):
        ss = frame.f_code.co_stacksize
        fn = frame.f_code.co_filename
        ln = frame.f_lineno
        co = linecache.getline(fn, ln).strip()
        print '%s %s:%s %s' % (ss * '>', fn, ln, co)
    sys.settrace(traceit)

def main():
    env = Environment(sys.argv)
    if env.is_debug():
        os.environ['PIDA_DEBUG'] = '1'
        os.environ['PIDA_LOG_STDERR'] = '1'
    else:
        warnings.filterwarnings("ignore")
    if env.is_trace():
        set_trace()
    if env.is_version():
        run_func = run_version
    else:
        run_func = run_pida
    exit_val = run_func(env)
    signal.signal(signal.SIGALRM, force_quit)
    signal.alarm(3)
    sys.exit(exit_val)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
