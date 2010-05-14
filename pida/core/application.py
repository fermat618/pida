# -*- coding: utf-8 -*-
"""
    pida.core.application
    ~~~~~~~~~~~~~~~~~~~~~

    This module handles starting up Pida..

    :copyright: 2007-2008 the Pida Project
    :license: GPL2 or later
"""
# system import(s)
import os
import sys
import warnings
import traceback

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
    gdk.threads_enter() # need to ensure threadsavety before any ui drawing
    if gtk.pygtk_version < (2, 8):
        die_cli(_('PIDA requires PyGTK >= 2.8. It only found %(major)s.%(minor)s')
                % {'major': gtk.pygtk_version[:2][0], 'minor': gtk.pygtk_version[:2][1]})
except ImportError, e:
    die_cli(_('PIDA requires Python GTK bindings. They were not found.'), e)


try:
    from pygtkhelpers.ui.dialogs import error
    def die_gui(message, exception):
        """Die in a GUI way."""
        error(_('Fatal error, cannot start PIDA'),
              long='%s\n%s' % (message, exception))
        die_cli(message)
except ImportError, e:
    die_cli(_('pygtkhelpers needs to be installed to run PIDA'), e)


# Python 2.5
if sys.version_info < (2, 5):
    die_gui(_('Python 2.5 is required to run PIDA. Only %(major)s.%(minor)s was found.') %
        {'major': sys.version_info[:2][0], 'minor': sys.version_info[:2][1]})


# Prevent PIDA from being run as root.
if os.getuid() == 0:
    die_gui("Pida should not be run as root", "Pida is dying")

# This can test if PIDA is installed
# also we have to import pdbus here so it gets initialized very early
try:
    import pida.core.pdbus
except ImportError, e:
    die_gui(_('The pida package could not be found.'), e)

from pida.core import environment
from pida.core.boss import Boss

def run_pida():
    #XXX: nasty compat hack
    import os
    os.environ['PIDA_PATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    b = Boss() #XXX: relocate firstrun

    # handle start params
    try:
        #XXX: this sucks, needs propper errors
        b.start() # might raise runtime error
        if environment.get_args():
            from pida.utils.gthreads import gcall
            gcall(b.cmd, 'buffer', 'open_files', files=environment.get_args()[1:])
        b.loop_ui()
        return 0
    except Exception, e:
        traceback.print_exc()
        die_gui("Pida has failed to start",  traceback.format_exc())
        return 1

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
    environment.parse_args(sys.argv)
    opts = environment.opts

    #options.create_default_manager(pida.core.environment.workspace_name())
    from pida.core import log
    log.setup()

    if not opts.debug:
        warnings.filterwarnings("ignore")

    if opts.trace:
        set_trace()

    # open workspace manager is asked for
    from pida.core.options import OptionsManager
    # we need a new optionsmanager so the default manager does not workspace
    # lookup yet
    om = OptionsManager(workspace="default")

    def do_workspace_manager():
        from pida.ui.window import WorkspaceWindow

        def kill(sm):
            sm.hide_and_quit()

        file_names = []

        if len(environment.get_args()) > 1:
            for i in environment.get_args()[1:]:
                file_names.append(os.path.abspath(i))

        def command(sw, row=None):
            # command dispatcher for workspace window
            opts.safe_mode = sw.safe_mode.get_active()
            if sw.user_action == "quit":
                sys.exit(0)
            elif sw.user_action == "new" and sw.new_workspace:
                opts.workspace = sw.new_workspace
                sw.hide_and_quit()
                gtk.main_quit()
            elif sw.user_action == "select":
                if row.id:
                    from pida.utils.pdbus import PidaRemote

                    pr = PidaRemote(row.id)
                    if file_names:
                        pr.call('buffer', 'open_files', file_names)

                    pr.call('appcontroller', 'focus_window')

                    sw.user_action = "quit"
                    sys.exit(0)
                else:
                    opts.workspace = row.workspace
                    sw.hide_and_quit()
                    gtk.main_quit()

        sw = WorkspaceWindow(command=command)
        sw.widget.show()
        #this mainloop will exit when the workspacewindow is closes
        gtk.main()


    if (om.open_workspace_manager() and not environment.workspace_set()) or \
        environment.workspace_manager():
        try:
            do_workspace_manager()
        except ImportError:
            warnings.warn_explicit('python DBus bindings not available. '
                        'Not all functions available.', Warning, 'pida', '')

    if opts.version:
        print _('PIDA, version %s') % pida.version
    elif opts.profile_path:
        print "---- Running in profile mode ----"
        import cProfile
        try:
            cProfile.runctx('run_pida()', globals(), locals(), opts.profile_path)
            #benchtime, stones = prof.runcall(run_pida)
        finally:
            pass
        #signal.signal(signal.SIGALRM, force_quit)
        #signal.alarm(3)
        print "---- Top 100 statistic ----"
        import pstats
        p = pstats.Stats(opts.profile_path)
        p.strip_dirs().sort_stats('time', 'cum').print_stats(100)

        sys.exit(0)

    else:
        exit_val = run_pida()
        #XXX: hack for killing threads - better soltions
        sys.exit(exit_val)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
