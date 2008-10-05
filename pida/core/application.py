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
import traceback

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


# Python 2.5
if sys.version_info < (2, 5):
    die_gui(_('Python 2.5 is required to run PIDA. Only %(major)s.%(minor)s was found.') %
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
    # handle start params
    from pida.core import environment
    if environment.get_args():
        from pida.utils.gthreads import gcall
        gcall(b.cmd, 'buffer', 'open_files', files=environment.get_args()[1:])
    try:
        start_success = b.start()
        b.loop_ui()
        return 0
    except Exception, e:
        traceback.print_exc()
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
    global opts
    from pida.core import environment
    environment.parse_args(sys.argv)
    opts = environment.opts
    
    from pida.core import options

    #options.create_default_manager(pida.core.environment.session_name())
    import pida.core.log
    pida.core.log.setup()
    
    if not opts.debug:
        warnings.filterwarnings("ignore")

    if opts.trace:
        set_trace()

    # open session manager is asked for
    from pida.core.options import OptionsManager
    from pida.utils.pdbus import list_pida_instances
    # we need a new optionsmanager so the default manager does not session
    # lookup yet
    om = OptionsManager(session="default")

    if (om.open_session_manager() and not environment.session_set()) or \
        environment.session_manager():
        from pida.ui.window import SessionWindow

        def kill(sm):
            sm.hide_and_quit()

        file_names = []

        if len(environment.get_args()) > 1:
            for i in environment.get_args()[1:]:
                file_names.append(os.path.abspath(i))

        def command(sw, row=None):
            # command dispatcher for session window
            opts.safe_mode = sw.safe_mode.get_active()
            if sw.user_action == "quit":
                sys.exit(0)
            elif sw.user_action == "new" and sw.new_session:
                opts.session = sw.new_session
                sw.hide_and_quit()
                gtk.main_quit()
            elif sw.user_action == "select":
                if row[0]:
                    from pida.utils.pdbus import PidaRemote

                    pr = PidaRemote(row[0])
                    if file_names:
                        pr.call('buffer', 'open_files', file_names)

                    pr.call('boss', 'focus_window')

                    sw.user_action = "quit"
                    sys.exit(0)
                else:
                    opts.session = row[3]
                    sw.hide_and_quit()
                    gtk.main_quit()

        sw = SessionWindow(command=command)
        sw.show_all()
        #this mainloop will exist when the sessionwindow is closes
        gtk.main()

    if opts.version:
        print _('PIDA, version %s') % PIDA_VERSION
    elif opts.profile_path:
        print "---- Running in profile mode ----"
        import hotshot, hotshot.stats, test.pystone
        prof = hotshot.Profile(opts.profile_path)
        prof.start()
        try:
            run_pida()
            #benchtime, stones = prof.runcall(run_pida)
        finally: 
            prof.stop()
            prof.close()
        
        #signal.signal(signal.SIGALRM, force_quit)
        #signal.alarm(3)
        print "---- Top 100 statistic ----"
        stats = hotshot.stats.load(opts.profile_path)
        #stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(100)

        sys.exit(0)

    else:
        exit_val = run_pida()
        #XXX: hack for killing threads - better soltions
        signal.signal(signal.SIGALRM, force_quit)
        signal.alarm(3)
        sys.exit(exit_val)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
