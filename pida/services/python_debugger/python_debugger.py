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


# Standard library imports
import os, sys, time, Queue, cgi

# kiwi imports
from kiwi.ui.objectlist import ObjectList, ObjectTree, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal

from pida.utils import rpdb2

# locale
from pida.core.locale import Locale
locale = Locale('python_debugger')
_ = locale.gettext


# rpdb2 overrides to force PIDA terminal use


class SessionManagerInternal(rpdb2.CSessionManagerInternal):
    
    def _spawn_server(self, fchdir, ExpandedFilename, args, rid):
        """
        Start an OS console to act as server.
        What it does is to start rpdb again in a new console in server only mode.
        """
        debugger = os.path.abspath(rpdb2.__file__)
        if debugger[-1] == 'c':
            debugger = debugger[:-1]
        baseargs = ['python', debugger, '--debugee', '--rid=%s' % rid]
        if fchdir:
            baseargs.append('--chdir')
        if self.m_fAllowUnencrypted:
            baseargs.append('--plaintext')
        #if self.m_fRemote:
        #    baseargs.append('--remote')
        if os.name == 'nt':
            baseargs.append('--pwd=%s' % self.m_pwd)
        if 'PGD_DEBUG' in os.environ:
            baseargs.append('--debug')
        baseargs.append(ExpandedFilename)
        cmdargs = baseargs + args.split()
        python_exec = sys.executable
        self.terminal.fork_command(python_exec, cmdargs)
        

class SessionManager(rpdb2.CSessionManager):
    
    def __init__(self, manager, pwd, fAllowUnencrypted, fAllowRemote, host):
        self.manager = manager
        smi = self._CSessionManager__smi = SessionManagerInternal(
                            pwd, 
                            fAllowUnencrypted, 
                            fAllowRemote, 
                            host
                            )
        smi.terminal = self

    def _create_view(self):
        view = Terminal(self.app)
        self.main_window.attach_slave('outterm_holder', view)
        return view

    def fork_command(self, *args, **kw):
        self.manager.terminal_view.fork_command(*args, **kw)


class DebuggerManager(object):
    """Control the debugging process and views"""
    
    def __init__(self, sm):
        self.connect_events()
        self.locals_view = LocalsViewer(sm)
        self.globals_view = GlobalsViewer(sm)
        self.stack_view = StackViewer(sm)
        self.threads_view = ThreadsViewer(sm)
        self.breaks_view = BreakpointViewer(sm)
        self.console_view = DebuggerConsole(sm)
        self.terminal_view = Terminal()

    def start_client(command_line, fAttach, fchdir, pwd, fAllowUnencrypted, fRemote, host):
        self.session_manager = SessionManager(self, pwd, fAllowUnencrypted, fRemote, host)

    def launch(self, commandline, change_directory=False):
        self.session_manager.launch(change_directory, commandline)

    def connect_events(self):
        event_type_dict = {rpdb2.CEventState: {}}
        self.session_manager.register_callback(self.on_update_state, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventStackFrameChange: {}}
        self.session_manager.register_callback(self.on_update_frame, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventThreads: {}}
        self.session_manager.register_callback(self.on_update_threads, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventNoThreads: {}}
        self.session_manager.register_callback(self.on_update_no_threads, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventNamespace: {}}
        self.session_manager.register_callback(self.on_update_namespace, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventThreadBroken: {}}
        self.session_manager.register_callback(self.on_update_thread_broken, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventStack: {}}
        self.session_manager.register_callback(self.on_update_stack, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventBreakpoint: {}}
        self.session_manager.register_callback(self.on_update_bp, event_type_dict, fSingleUse = False)

    def on_update_state(self, state):
        print 'us', state.m_state
        self.c.write_info(state.m_state + '\n')
        if state.m_state == 'detached':
            print 'stopping'
            os.kill(PID, 9)
            gtk.main_quit()
            self.session_manager.stop()

    def on_update_frame(self, event):
        print 'uf', event
        gobject.idle_add(self.s.select_frame, event.m_frame_index)

    def on_update_namespace(self, *args):
        print 'un', args
        gobject.idle_add(self.l.update_namespace)
        gobject.idle_add(self.g.update_namespace)

    def on_update_stack(self, event):
        print 'uk', event
        gobject.idle_add(self.s.update_stack, event.m_stack)

    def on_update_bp(self, event):
        print 'ub', event
        def _u(event):
            act = event.m_action
            if event.m_bp is not None:
                filename = event.m_bp.m_filename
                linenumber = event.m_bp.m_lineno
                index = event.m_bp.m_id
                indices = None
            else:
                filename = None
                linenumber = None
                index = None
                indices = event.m_id_list
            self.b.update_bp(act, index, indices, filename, linenumber)
            #self.master.update_bp(act, index, indices, filename, linenumber)
        gobject.idle_add(_u, event)

    def on_update_no_threads(self, *args):
        print 'unt', args

    def on_update_threads(self, event):
        print 'ut', event, dir(event)
        gobject.idle_add(self.t.update_threads, event.m_thread_list, event.m_current_thread)

    def on_update_thread_broken(self, *args):
        print 'utb', args

# Service class
class Python_debugger(Service):
    """Describe your Service Here""" 

# Required Service attribute for service loading
Service = Python_debugger



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
