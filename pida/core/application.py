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
import warnings
import atexit

def die_cli(message):
    """Die in a command line way."""
    print message
    print 'Exiting. (this is fatal)'
    sys.exit(1)


# First gtk import, let's check it
try:
    import gtk, gtk.gdk
    if gtk.pygtk_version < (2, 8):
        die_cli('PIDA requires PyGTK >= 2.8. It only found %s.%s'
                % gtk.pygtk_version[:2])
except ImportError:
    die_cli('PIDA requires Python GTK bindings. They were not found.')

gtk.gdk.threads_init()

try:
    from kiwi.ui.dialogs import error
    def die_gui(message):
        """Die in a GUI way."""
        error("Fatal error, cannot start PIDA", 
              message)
        die_cli(message)

except ImportError:
    die_cli('Kiwi needs to be installed to run PIDA')


# Python 2.4
if sys.version_info < (2,4):
    die_gui('Python 2.4 is required to run PIDA. Only %s.%s was found.' %
            sys.version_info[:2])


# This can test if PIDA is installed
try:
    from pida.core.environment import Environment
    from pida.core.boss import Boss
    from pida import PIDA_VERSION
except ImportError:
    die_gui('The pida package could not be found.')


def run_version(env):
    print 'PIDA, version %s' % PIDA_VERSION
    return 0

def run_pida(env):
    b = Boss(env)
    b.start()
    gtk.gdk.threads_enter()
    b.loop_ui()
    gtk.gdk.threads_leave()
    return 0

def main():
    env = Environment(sys.argv)
    if env.is_debug():
        os.environ['PIDA_DEBUG'] = '1'
        os.environ['PIDA_LOG_STDERR'] = '1'
    else:
        warnings.filterwarnings("ignore")
    if env.is_version():
        run_func = run_version
    else:
        run_func = run_pida
    exit_val = run_func(env)
    sys.exit(exit_val)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
