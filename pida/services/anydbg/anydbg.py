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

import os

import gtk

from configobj import ConfigObj

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.environment import get_pixmap_path
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectControllerMananger, ProjectController, \
    ProjectKeyDefinition

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal
from pida.ui.buttons import create_mini_button

from pida.utils.gthreads import GeneratorTask, gcall

class AnyDbg_Debugger:
    def __init__(self, executable, parameters, service):
        self._executable = executable
        self._parameters = parameters
        self.svc = service

    def set_executable(self, executable):
        self._executable = executable

    def set_parameters(self, parameters):
        self._parameters = parameters

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def step_in(self):
        raise NotImplementedError

    def step_over(self):
        raise NotImplementedError

    def toggle_breakpoint(self):
        raise NotImplementedError

class AnyDbg_gdb_interface(AnyDbg_Debugger):
    def _send_command(self,command):
        self._console._term.feed_child(cmd + '\n')
    
    def _parse(self, data):
        print "| "+data

    def _jump_to_line(self, file, line):
        self.svc.boss.editor.cmd('open', document=file)
        self.svc.boss.editor.cmd('goto_line', line=line)

    def init(self):
        self._console = svc.boss.cmd('commander','execute',
                                            commandargs=[self.GDB_EXEC],
                                            cwd=os.getcwd(), 
                                            title="pydb",
                                            icon=None,
                                            use_python_fork=True,
                                            parser_func = self.parse)
        # match '(%%PATH%%:%%LINE%%):  <module>'
        self._console._term.match_add_callback('jump_to','^\(.*:.*\):.*$', '', _jump_to_line)

        if self.executable != None:
            self._send_command('file '+self.executable)
        
    def start(self):
        """
        First time start: launch the debugger
        Second time start: continue debugging
        """
        if self._console == None:
            self.init()
            self._send_command('run')
        else:
            self._send_command('continue')

    def stop(self):
        """
        First time stop: pause the debugging
        Second time stop: end the debugger
        """
        if self._console == None:
            self.window.error_dlg('Tried to stop a non-working debugger')
        # TODO

    def step_in(self):
        self._send_command('step')

    def step_over(self):
        self._send_command('next')

    def finish(self):
        self._send_command('finish')

    def add_breakpoint(self, file, line):
        self._send_command('break '+file+':'+line)

    def del_breakpoint(self, file, line):
        self._send_command('clear '+file+':'+line)

class AnyDbg_pydb(AnyDbg_Debugger):
    GDB_EXEC = "/usr/bin/pydb"

class AnyDbg_gdb(AnyDbg_Debugger):
    GDB_EXEC = "/usr/bin/gdb"

class AnyDbg_bash(AnyDbg_Debugger):
    GDB_EXEC = "/usr/bin/bashdb"

# Actions
class AnyDbgActionsConfig(ActionsConfig):
    def create_actions(self):
        # Menu
        self.create_action(
            'show_breakpoints_view',
            TYPE_TOGGLE,
            'Debugger breakpoints list',
            'Show the breakpoints list',
            'accessories-text-editor',
            self.on_show_breakpoints_view,
            '<Shift><Control>b',
        )
        self.create_action(
            'show_stack_view',
            TYPE_TOGGLE,
            "Debugger's stack view",
            'Show the stack of current debugger',
            'accessories-text-editor',
            self.on_show_stack_view,
            '<Shift><Control>s',
        )
        self.create_action(
            'show_console_view',
            TYPE_TOGGLE,
            "Debugger's console",
            'Show the console of the debugger',
            'accessories-text-editor',
            self.on_show_console_view,
            '<Shift><Control>c',
        )

        # Toolbar
        self.create_action(
            'step_over',
            TYPE_NORMAL,
            'Step Over',
            'Step over highlighted statement',
            gtk.STOCK_MEDIA_FORWARD,
            self.on_step_over,
            '<F6>',
        )
        self.create_action(
            'step_in',
            TYPE_NORMAL,
            'Step In',
            'Step in highlighted statement',
            gtk.STOCK_MEDIA_NEXT,
            self.on_step_in,
            '<F5>',
        )
        self.create_action(
            'dbg_start',
            TYPE_NORMAL,
            'Break',
            'Stop debbuging',
            gtk.STOCK_MEDIA_PAUSE,
            self.on_stop,
            '<F4>',
        )
        self.create_action(
            'dbg_stop',
            TYPE_NORMAL,
            'Continue',
            'Start debugger or Continue debbuging',
            gtk.STOCK_MEDIA_PLAY,
            self.on_start,
            '<F3>',
        )
        self.create_action(
            'toggle_breakpoint',
            TYPE_NORMAL,
            'Toggle breakpoint',
            'Toggle breakpoint on selected line',
            gtk.STOCK_MEDIA_RECORD,
            self.on_toggle_breakpoint,
            '<F3>',
        )

    # Buttonbar
    def on_step_over(self):
        self.svc.dbg.step_over()

    def on_step_in(self):
        self.svc.dbg.step_in()

    def on_start(self):
        self.svc.dbg.start()
    def on_stop(self):
        self.svc.dbg.stop()

    # Menu
    def on_show_breakpoints_view(self, action):
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._breakpoints_view)

    def on_show_stack_view(self, action):
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._stack_view)
        
    def on_show_console_view(self, action):
        if self.svc.dbg != None:
            self.boss.cmd('window', 'add_view', paned='Terminal', view=self.svc.dbg._console)
        else:
            self.window.error_dlg('No debugger is running')

    #
    def on_toggle_breakpoint(self, file, line):
        self.svc.emit('toggle_breakpoint')

# Events
class AnyDbgEventsConfig(EventsConfig):
    def create_events(self):
        self.create_event('launch_debugger')

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
                                     self.on_document_changed)
        self.subscribe_foreign_event('editor', 'started',
                                     self.on_editor_startup)

    def on_document_changed(self, document):
        pass

    def on_editor_startup(self):
        """
        Set the highlights in vim
        TODO move this to vim startup file and/or create a highlight preference
        """
        self.svc.boss.editor.cmd('define_sign_type', type="breakpoint", icon=get_pixmap_path("stop.svg"), 
                                                linehl="", text="X", texthl="Search")
        self.svc.boss.editor.cmd('define_sign_type', type="step", icon=get_pixmap_path("forward.svg"), 
                                                linehl="lCursor", text=">", texthl="lCursor")

    def on_breakpoint_tog(self, file, line):
        """
        Toggles a breakpoint on line of file and store it with the current controller
        """
        if not self.svc._controller.store_breakpoint(file, line):
            self.svc._controller.flush_breakpoint(file, line)
            return False
        return True
        
    def on_stack_push(self, function):
        """
        Pushes a function call in the stack
        """
        pass
        
    def on_stack_pop(self, function):
        """
        Pops a function call in the stack
        """
        pass


# Controller
class GenericDebuggerController(ProjectController):

    name = 'GENERIC_DEBUGGER'

    label = 'Generic Debugger'

    attributes = [
        ProjectKeyDefinition('executable', 'Path to the executable', True),
        ProjectKeyDefinition('parameters', 'Parameters to give to the executable', True),
        ProjectKeyDefinition('debugger', 'Choose your debugger', True),
    ] + ProjectController.attributes

    def execute(self):
        executable = self.get_option('executable')
        parameters = self.get_option('parameters')
        debugger = self.get_option('debugger')
        if not debugger or not executable or not parameters:
            self.boss.get_window().error_dlg(
                'Debugger is not fully configured yet.' 
            )
        else:
            self.boss.get_service('debugger').emit('launch_debugger',executable,parameters,debugger,self)
    
    def store_breakpoint(self, file, line):
        bplist = self.get_option('breakpoints')
        if (file, line) not in bplist:
            bplist.append((file, line))
            return True
        return False

    def flush_breakpoint(self, file, line):
        bplist = self.get_option('breakpoints')
        if (file, line) in bplist:
            bplist.remove((file, line))
            return False
        return True

    def list_breakpoints(self):
        return self.get_option('breakpoints')
        
class AnyDbgFeaturesConfig(FeaturesConfig):

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController,
            GenericDebuggerController)

# Service class
class Debugger(Service):
    """Debugging a project service""" 

    actions_config = AnyDbgActionsConfig
    events_config = AnyDbgEventsConfig
    features_config = AnyDbgFeaturesConfig

    def start(self):
        """
        Starts the service
        """
        self._anydbg = {}
        self.dbg = None
        self.register_debugger('pydb', AnyDbg_pydb) # TODO: dynamic loading
        self.register_debugger('gdb', AnyDbg_gdb)   # TODO: dynamic loading
        self.subscribe_event('launch_debugger',self.init_dbg_session)

        self._breakpoints_view = None
        self._stack_view = None

        # Sets default sensitivity for button bar
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)
        self.get_action('dbg_start').set_sensitive(False)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('toggle_breakpoint').set_sensitive(False)

    def init_dbg_session(self, executable, parameters, debugger, controller):
        """
        Initiates the debugging session
        """
        self.dbg = self._anydbg[debugger]()
        self.dbg.set_executable(executable)
        self.dbg.set_parameters(parameters)
        self._controller = controller

        self.get_action('dbg_start').set_sensitive(True)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)

    def register_debugger(self, name, classname):
        """
        Registers a new debugger class
        """
        self._anydbg[name] = classname

    def set_current_doc(self, document):
        """
        Sets current document to document
        Updates the editor if breakpoints exist for current doc
        @param document to change to
        """
        self.current_document = document

# Required Service attribute for service loading
Service = Debugger

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
