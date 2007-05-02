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
import re

import gtk

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE
from pida.core.environment import get_pixmap_path
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectController, \
    ProjectKeyDefinition

from pida.ui.views import PidaView
from pida.ui.buttons import create_mini_button

from pida.utils.gthreads import GeneratorTask, gcall

# --- Function stack view

class AnyDbgStackItem(object):
    def __init__(self, function):
        self.function = function

class AnyDbgStackView(PidaView):
    label_text = 'Debug Function Stack'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self._breakpoints = {}
        self._breakpoint_list = ObjectList(
            [
                Column('function', sorted=True),
            ]
        )
        self._breakpoint_list.connect('double-click', self._on_stack_double_click)
        self.add_main_widget(self._breakpoint_list)
        self._breakpoint_list.show_all()

        self.svc.subscribe_event('function_call', self.on_function_call)
        self.svc.subscribe_event('function_return', self.on_function_return)
        self.svc.subscribe_event('step', self.on_step)

    def on_function_call(self):
        print "TODO: CALL"

    def on_function_return(self):
        print "TODO: RET"

    def on_step(self, file, line, function):
        print "TODO: STEP", file, line, function

    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def push_function(self, function):
        func = AnyDbgStackItem(function)
        if function not in self._stack:
            self._stack[(function)] = func
            self._stack_list.append(function) # XXX manage it as a stack
            return True
        else:
            return False
    
    def pop_function(self, function):
        if (function) in self._stack:
            self._stack_list.remove(self._stack[function])
            del(self._stack[function])
            return True
        else:
            return False

    def get_stack(self):
        return self._stack
    
    def _on_stack_double_click(self, olist, item):
        pass

# --- Breakpoint list view

class AnyDbgBreakPointItem(object):
    def __init__(self, file, line):
        self.file = file
        self.line = line

class AnyDbgBreakPointsView(PidaView):
    label_text = 'Debug Breakpoints'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self._breakpoints = {}
        self._breakpoint_list = ObjectList(
            [
                Column('line', sorted=True),
                Column('file'),
            ]
        )
        self._breakpoint_list.connect('double-click', self._on_breakpoint_double_click)
        self.add_main_widget(self._breakpoint_list)
        self._breakpoint_list.show_all()

        self.svc.subscribe_event('add_breakpoint', self.add_breakpoint)
        self.svc.subscribe_event('del_breakpoint', self.del_breakpoint)

    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def add_breakpoint(self, ident, file, line):
        breakpoint = AnyDbgBreakPointItem(file, line)
        if (file, line) not in self._breakpoints:
            self._breakpoints[(file,line)] = breakpoint
            self._breakpoint_list.append(breakpoint)
            return True
        else:
            return False
    
    def del_breakpoint(self, file, line):
        if (file, line) in self._breakpoints:
            self._breakpoint_list.remove(self._breakpoints[(file, line)])
            del(self._breakpoints[(file, line)])
            return True
        else:
            return False

    def get_breakpoint_list(self):
        return self._breakpoints
    
    def _on_breakpoint_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)
        self.svc.boss.editor.cmd('open', document=item.file)

class AnyDbg_Debugger:
    def __init__(self, executable, parameters, service):
        self._executable = executable
        self._parameters = parameters
        self.svc = service

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def step_in(self):
        raise NotImplementedError

    def step_over(self):
        raise NotImplementedError

    def toggle_breakpoint(self, file, line):
        raise NotImplementedError

class AnyDbg_gdb_interface(AnyDbg_Debugger):
    _console = None
    _breakpoints = []

    _parser_patterns = {
        # line: Restarting <EXEC> with arguments: <ARGS>
        'Restarting (.*) with arguments:(.*)' : 
            lambda self, m: self.svc.emit('start_debugging', 
                                                    executable=m.group(1), 
                                                    arguments=m.group(2)),
        # line: *** Blank or comment
        '\*\*\* Blank or comment' : None,
        # line: Breakpoint <N> set in file <FILE>, line <LINE>.
        'Breakpoint (\d+) set in file (.*), line (\d+).' :
            lambda self, m: self.svc.emit('add_breakpoint', 
                                        ident=m.group(1), 
                                        file=m.group(2),
                                        line=m.group(3)),
        # line: Deleted breakpoint <N>
        'Deleted breakpoint (\d+)' :
            lambda self, m: self.svc.emit('del_breakpoint', ident=m.group(1)),
        # line: (<PATH>:<LINE>):  <FUNCTION>
        '\((.*):(\d+)\): (.*)' :
            lambda self, m: self.svc.emit('step', file=m.group(1), 
                                                  line=m.group(2), 
                                                  function=m.group(3)),
        '--Call--' : 
            lambda self, m: self.svc.emit('function_call'),
        '--Return--' : 
            lambda self, m: self.svc.emit('function_return')
    }
                
    def _parse(self, data):
        for pattern in self._parser_patterns:
            m = re.search(pattern, data)
            if m is not None:
                if self._parser_patterns[pattern] is not None:
                    self._parser_patterns[pattern](self,m)

    def _send_command(self,command):
        os.write(self._console.master, command + '\n')

    def _jump_to_line(self, event, data):
        m = re.search('^\((.*):(.*)\):.*$', data)
        if m is not None:
            self.svc.boss.editor.cmd('open', document=m.group(1))
            self.svc.boss.editor.cmd('goto_line', line=m.group(2))

    def init(self):
        self._console = self.svc.boss.cmd('commander','execute',
                                            commandargs=[self.GDB_EXEC],
                                            cwd=os.getcwd(), 
                                            title="pydb",
                                            icon=None,
                                            use_python_fork=True,
                                            parser_func = self._parse)
        # match '(%%PATH%%:%%LINE%%):  <module>'
        self._console._term.match_add_callback('jump_to','^\(.*:.*\):.*$', 
                                                '^\((.*):(.*)\):.*$', self._jump_to_line)

        if self._executable != None:
            self._send_command('file '+self._executable)
    
    def end(self):
        self._console.close_view()
        self._console = None
        self.svc.end_dbg_session()

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

    __stop_state = False
    def stop(self):
        """
        First time stop: reinit the debugger
        Second time stop: end the debugger
        """
        if self._console == None:
            self.window.error_dlg('Tried to stop a non-working debugger')
        if self.__stop_state is False:
            self._send_command('run')
            self.__stop_state = True
        else:
            self.end()

    def step_in(self):
        self._send_command('step')

    def step_over(self):
        self._send_command('next')

    def finish(self):
        self._send_command('finish')

    def toggle_breakpoint(self, file, line):
        if (file, line) not in self._breakpoints:
            self._breakpoints.append((file, line))
            self.add_breakpoint(file, line)
        else:
            self._breakpoints.remove((file, line))
            self.del_breakpoint(file, line)
    
    def add_breakpoint(self, file, line):
        self._send_command('break '+file+':'+str(line))

    def del_breakpoint(self, file, line):
        self._send_command('clear '+file+':'+str(line))

class AnyDbg_pydb(AnyDbg_gdb_interface):
    GDB_EXEC = "/usr/bin/pydb"

class AnyDbg_gdb(AnyDbg_gdb_interface):
    GDB_EXEC = "/usr/bin/gdb"

class AnyDbg_bash(AnyDbg_gdb_interface):
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
            'dbg_start',
            TYPE_NORMAL,
            'Continue',
            'Start debugger or Continue debbuging',
            gtk.STOCK_MEDIA_PLAY,
            self.on_start,
            '<F3>',
        )
        self.create_action(
            'dbg_stop',
            TYPE_NORMAL,
            'Break',
            'Stop debbuging',
            gtk.STOCK_MEDIA_PAUSE,
            self.on_stop,
            '<F4>',
        )
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
            'toggle_breakpoint',
            TYPE_NORMAL,
            'Toggle breakpoint',
            'Toggle breakpoint on selected line',
            gtk.STOCK_MEDIA_RECORD,
            self.on_toggle_breakpoint,
            '<F3>',
        )

    # Buttonbar
    def on_step_over(self, action):
        self.svc.dbg.step_over()

    def on_step_in(self, action):
        self.svc.dbg.step_in()

    def on_start(self, action):
        self.svc.dbg.start()

    def on_stop(self, action):
        self.svc.dbg.stop()

    # Menu
    def on_show_breakpoints_view(self, action):
        if not self.svc._breakpoints_view:
            self.svc._breakpoints_view = AnyDbgBreakPointsView(self.svc)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._breakpoints_view)

    def on_show_stack_view(self, action):
        if not self.svc._stack_view:
            self.svc._stack_view = AnyDbgStackView(self.svc)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._stack_view)
        
    def on_show_console_view(self, action):
        if self.svc.dbg != None:
            self.svc.boss.cmd('window', 'add_view', paned='Terminal', view=self.svc.dbg._console)
        else:
            self.svc.window.error_dlg('No debugger is running')

    #
    def on_toggle_breakpoint(self, action):
        self.svc.emit('toggle_breakpoint', file=self.svc._current.get_filename(),
                        line=self.svc.boss.editor.cmd('get_current_line_number'))

# Events
class AnyDbgEventsConfig(EventsConfig):
    def create_events(self):
        # UI events
        self.create_event('launch_debugger')
        self.create_event('toggle_breakpoint')

        # Debugger events
        self.create_event('start_debugging')
        self.create_event('step')
        self.create_event('function_call')
        self.create_event('function_return')
        self.create_event('add_breakpoint')
        self.create_event('del_breakpoint')

        self.subscribe_event('toggle_breakpoint', self.on_toggle_breakpoint)
        self.subscribe_event('launch_debugger',self.on_launch_debugger)
        self.subscribe_event('add_breakpoint', self.on_add_breakpoint)
        self.subscribe_event('start_debugging', self.on_start_debugging)

    def on_launch_debugger(self, executable, parameters, debugger, controller):
        if self.svc.dbg is not None:
            self.svc.window.error_dlg('Debugging session already running.')
        else:
            self.svc.init_dbg_session(executable, parameters, debugger, controller)

    def on_toggle_breakpoint(self, file, line):
        """
        Toggles a breakpoint on line of file
        Store the breakpoint and mark it as unverified
        """
        if self.svc.dbg != None:
            self.svc.dbg.toggle_breakpoint(file, line)
        else:
            self.svc._controller.prestore_breakpoint(file, line)

    def on_add_breakpoint(self, ident, file, line):
        """
        Add a breakpoint on line of file
        Store it with the current controller
        """
        self.svc._controller.store_breakpoint(ident, file, line)

    def on_del_breakpoint(self, ident, file, line):
        """
        Deletes a breakpoint on line of file 
        Store it with the current controller
        """
        self.svc._controller.flush_breakpoint(ident, file, line)
        
    def on_start_debugging(self, executable, arguments):
        self.svc.get_action('step_in').set_sensitive(True)
        self.svc.get_action('step_over').set_sensitive(True)
        self.svc.get_action('dbg_start').set_sensitive(True)
        self.svc.get_action('dbg_stop').set_sensitive(True)

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
                                     self.on_document_changed)
        self.subscribe_foreign_event('editor', 'started',
                                     self.on_editor_startup)

    def on_editor_startup(self):
        """
        Set the highlights in vim
        TODO move this to vim startup file and/or create a highlight preference
        """
        self.svc.boss.editor.cmd('define_sign_type', type="breakpoint", icon=get_pixmap_path("stop.svg"), 
                                                linehl="", text="X", texthl="Search")
        self.svc.boss.editor.cmd('define_sign_type', type="step", icon=get_pixmap_path("forward.svg"), 
                                                linehl="lCursor", text=">", texthl="lCursor")

    def on_document_changed(self, document):
        if document != None:
            self.svc.get_action('toggle_breakpoint').set_sensitive(True)
            self.svc.update_editor(document)
        else:
            self.svc.get_action('toggle_breakpoint').set_sensitive(False)

# Controller
class GenericDebuggerController(ProjectController):

    name = 'GENERIC_DEBUGGER'

    label = 'Generic Debugger'

    attributes = [
        ProjectKeyDefinition('executable', 'Path to the executable', True),
        ProjectKeyDefinition('parameters', 'Parameters to give to the executable', True),
        ProjectKeyDefinition('debugger', 'Choose your debugger', True),
    ]# + ProjectController.attributes

    def execute(self):
        executable = self.get_option('executable')
        parameters = self.get_option('parameters')
        debugger = self.get_option('debugger')
        if not debugger or not executable:
            self.boss.get_window().error_dlg(
                'Debug controller is not fully configured.' 
            )
        else:
            self.boss.get_service('anydbg').emit('launch_debugger',
                                                 executable=executable,
                                                 parameters=parameters,
                                                 debugger=debugger,
                                                 controller=self)

    __prebpoints = [] # TODO: save it with the controller
    def prestore_breakpoint(self, file, line):
        if (file, line) not in self.__prebpoints:
            self.__prebpoints.append((file, line))
            return True
        return False

    _breakpoints = {}

#set_option('breakpoints', [1,2,3,4])
    __bpoints = [] # TODO: save it with the controller
    def store_breakpoint(self, ident, file, line):
        self._breakpoints[ident] = (file, line)
        if (file, line) not in self.__bpoints:
            self.__bpoints.append((file, line))

    def flush_breakpoint(self, ident):
        if ident in self._breakpoints:
            (file, line) = self._breakpoints[ident]
            if (file, line) in self.__bpoints:
                self.__bpoints.remove((file, line))

    def list_prestored_breakpoints(self):
        l = self.get_option('pre_breakpoints')
        if l == None:
            return []
        return l

    def list_breakpoints(self):
        l = self.get_option('breakpoints')
        if l == None:
            return []
        return l
        
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
        self._controller = None
        self.dbg = None
        self.register_debugger('pydb', AnyDbg_pydb) # TODO: dynamic loading
        self.register_debugger('gdb', AnyDbg_gdb)   # TODO: dynamic loading

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
        self.dbg = self._anydbg[debugger](executable, parameters, self)
        self._controller = controller

        self.get_action('dbg_start').set_sensitive(True)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)

        for (file, line) in self._controller.list_prestored_breakpoints():
            self.emit('toggle_breakpoint', file, line)

    def end_dbg_session(self):
        """
        Ends the debugging session
        """
        self.dbg = None

        self.get_action('dbg_start').set_sensitive(False)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)

    def update_editor(self, document):
        """
        Updates the editor with current's document breakpoints
        """
        self._current = document
        if self._controller is not None:
            for (file, line) in self._controller.list_breakpoints():
                if document.get_filename() == file:
                    self.boss.editor.cmd('show_sign', type='breakpoint', 
                                                      filename=file,
                                                      line=line)

    def register_debugger(self, name, classname):
        """
        Registers a new debugger class
        """
        self._anydbg[name] = classname

# Required Service attribute for service loading
Service = Debugger

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
