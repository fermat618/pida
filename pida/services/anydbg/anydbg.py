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

        self.svc.subscribe_event('function_call', on_function_call)
        self.svc.subscribe_event('function_return', on_function_return)
        self.svc.subscribe_event('step', on_step)
        

    def on_function_call(self):
        print "VCALL"

    def on_function_return(self):
        print "VRET"

    def on_step(self, file, line, function):
        print "VSTEP"

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
        if (func) in self._stack:
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

        self.svc.subscribe_event('add_breakpoint', add_breakpoint)
        self.svc.subscribe_event('del_breakpoint', del_breakpoint)

    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def add_breakpoint(self, file, line):
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

    def toggle_breakpoint(self):
        raise NotImplementedError

class AnyDbg_gdb_interface(AnyDbg_Debugger):
    _console = None

    def _send_command(self,command):
        os.write(self._console.master, command + '\n')
    
    def _parse(self, data):
        print "debugger rcpt: "+data

# when starting
# line: Restarting /home/guyzmo/Workspace/Perso/pIDA/pida-svn/bin/pida with arguments:
        m = re.search('Restarting (.*) with arguments:(.*)',data)
        if m:
            self.svc.emit('start_debugging', executable=m.group(1), 
                                             arguments=m.group(2))

# when break <file>:<line>
# line: *** Blank or comment
        m = re.search('\*\*\* Blank or comment', data)
        if m:
            print "blank breakpoint"

# line: Breakpoint 1 set in file /home/guyzmo/Workspace/Perso/pIDA/pida-svn/pida/services/commander/commander.py, line 218.
        m = re.search('Breakpoint (\d+) set in file (.*), line (\d+).', data)
        if m:
            self.svc.emit('add_breakpoint', ident=m.group(1), 
                                            file=m.group(2),
                                            line=m.group(3))

# when clear <file>:<line>
# line: Deleted breakpoint 1
        m = re.search('Deleted breakpoint (\d+)', data)
        if m:
            self.svc.emit('del_breakpoint', ident=m.group(1))

# when step / next / finish
# line: (/home/guyzmo/Workspace/Perso/pIDA/pida-svn/bin/pida:28):  <module>
        m = re.search('\((.*):(\d+)\): (.*)', data)
        if m:
            self.svc.emit('step', file=m.group(1), 
                                  line=m.group(2), 
                                  function=m.group(3))
# line: --Call--
        m = re.search('--Call--', data)
        if m:
            self.svc.emit('function_call')
# line: --Return--
        m = re.search('--Return--', data)
        if m:
            self.svc.emit('function_return')


    def _jump_to_line(self, event, data):
        pass
#        self.svc.boss.editor.cmd('open', document=file)
#        self.svc.boss.editor.cmd('goto_line', line=line)

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
            self.svc._breakpoints_view = AnyDbgBreakPointsView(self)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._breakpoints_view)

    def on_show_stack_view(self, action):
        if not self.svc._stack_view:
            self.svc._stack_view = AnyDbgStackView(self)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._stack_view)
        
    def on_show_console_view(self, action):
        if self.svc.dbg != None:
            self.svc.boss.cmd('window', 'add_view', paned='Terminal', view=self.svc.dbg._console)
        else:
            self.svc.window.error_dlg('No debugger is running')

    #
    def on_toggle_breakpoint(self, file, line):
        self.svc.emit('toggle_breakpoint')

# Events
class AnyDbgEventsConfig(EventsConfig):
    def create_events(self):
        self.create_event('launch_debugger')
        self.create_event('start_debugging')
        self.create_event('step')
        self.create_event('function_call')
        self.create_event('function_return')
        self.create_event('add_breakpoint')
        self.create_event('del_breakpoint')

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
        self.dbg = self._anydbg[debugger](executable, parameters, self)
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
