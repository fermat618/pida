# -*- coding: utf-8 -*- 
"""
    pida.core.application
    ~~~~~~~~~~~~~~~~~~~~~

    this module handle starting up pida

    :copyright: 
        * 2007      Ali Afshar
        * 2007-2008 Ronny Pfannschmidt

    :license: GPL2 or later
"""
# system import(s)
import os
import sys
import signal
import warnings

from pida.core.signalhandler import handle_signals

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
    from pida.core.environment import opts
    from pida.core.boss import Boss
    from pida import PIDA_VERSION
except ImportError, e:
    die_gui(_('The pida package could not be found.'), e)


def run_pida():
    b = Boss()
    handle_signals(b)
    try:
        start_success = b.start()
        gdk.threads_enter()
        b.loop_ui()
        gdk.threads_leave()
        return 0
    except Exception, e:
        print e
        return 1

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
        for k, i in frame.f_locals.items():
            try:
                print '%s=%s' % (k, i)
            except:
                print k, 'unable to print value'
        print
    sys.settrace(traceit)

def main():
    if not opts.debug:
        warnings.filterwarnings("ignore")

    if opts.trace:
        set_trace()

    if opts.version:
        print _('PIDA, version %s') % PIDA_VERSION
    else:
        exit_val = run_pida()
        #XXX: hack for killing threads - better soltions
        signal.signal(signal.SIGALRM, force_quit)
        signal.alarm(3)
        sys.exit(exit_val)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
