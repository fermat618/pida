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
    def __init__(self, frame, function, file, line):
        self.frame = frame
        self.function = function
        self.file = file
        self.line = line
        self.parent = None

class AnyDbgStackView(PidaView):
    label_text = 'Debug Function Stack'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self.__last = None
        self.__call = False
        self.__return = False
        self.__cnt = 0
        self._stack_list = ObjectList(
            [
                Column('frame'), 
                Column('line'),
                Column('function'),
                Column('file'),
            ]
        )
        self._stack_list.connect('double-click', self._on_frame_double_click)
        self.add_main_widget(self._stack_list)
        self._stack_list.show_all()

        self.svc.subscribe_event('function_call', self.on_function_call)
        self.svc.subscribe_event('function_return', self.on_function_return)
        self.svc.subscribe_event('step', self.on_step)

    def on_function_call(self):
        self.__call = True

    def on_function_return(self):
        self.__return = True

    def on_step(self, file, line, function):
        if self.__return is True:
            self.pop_function()
            self.__return = False

        if self.__call is True:
            self.push_function(function, file, line)
            self.__call = False

        if self.__call is False and self.__return is False:
            if self.__last is None:
                self.push_function(function, file, line)
            else:
                self.pop_function()
                self.push_function(function, file, line)

        return True

    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def push_function(self, function, file, line):
        func = AnyDbgStackItem(self.__cnt, function, file, line)
        func.parent = self.__last
        self._stack_list.insert(0, func)
        self.__last = func
    
    def pop_function(self):
        if self.__last is not None:
            self._stack_list.remove(self.__last)
            self.__last = self.__last.parent

    def _on_frame_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.file)

# --- Breakpoint list view

class AnyDbgBreakPointItem(object):
    def __init__(self, file, line, status='enabled'):
        self.file = file
        self.line = line
        self.status = status

class AnyDbgBreakPointsView(PidaView):
    label_text = 'Debug Breakpoints'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self._breakpoints = {}
        self._breakpoint_list = ObjectList(
            [
                Column('line'),
                Column('file', sorted=True),
                Column('status')
            ]
        )
        self._breakpoint_list.connect('double-click', self._on_breakpoint_double_click)
        self.add_main_widget(self._breakpoint_list)
        self._breakpoint_list.show_all()

        if self.svc._controller:
            for file in self.svc._controller.list_prestored_breakpoints():
                line = self.svc._controller.list_prestored_breakpoints()[file]
#                print "TOG1", file, line
                self.add_breakpoint(None, file, line)

            for file in self.svc._controller.list_breakpoints():
                line = self.svc._controller.list_breakpoints()[file]
#                print "TOG1", file, line
                self.add_breakpoint(None, file, line)

        self.svc.subscribe_event('add_breakpoint', self.add_breakpoint)
        self.svc.subscribe_event('del_breakpoint', self.del_breakpoint)

    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def add_breakpoint(self, ident, file, line):
        if self.svc.dbg is None:
            breakpoint = AnyDbgBreakPointItem(file, line, 'disabled')
        else:
            breakpoint = AnyDbgBreakPointItem(file, line)

        if (file, line) not in self._breakpoints:
            self._breakpoints[(file,line)] = breakpoint
            self._breakpoint_list.append(breakpoint)
            return True
        elif (file, line) in self._breakpoints:
            if self._breakpoints[(file, line)].status == 'disabled':
                self._breakpoints[(file, line)].status == 'enabled'
        else:
            return False
    
    def del_breakpoint(self, ident, file, line):
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
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.file)

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

    def _jump_to_line(self, event, data, foo=None):
        m = re.search('^\((.*):(.*)\):.*$', data)
        if m is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=m.group(1))
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

        self.subscribe_event('step', self.on_step)

    def on_step(self, file, line, function):
        self.svc.boss.cmd('buffer', 'open_file', file_name=file)
        if self.svc._current != None and self.svc._current.get_filename() == file:
            if self.svc._step is not None:
                (oldfile, oldline) = self.svc._step
                self.svc.boss.editor.cmd('hide_sign', type='step', 
                                                        file_name=oldfile,
                                                        line=oldline)
            self.svc.boss.editor.cmd('goto_line', line=line)
            self.svc.boss.editor.cmd('show_sign', type='step', 
                                                    file_name=file,
                                                    line=line)
            self.svc._step = (file, line)

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
        if self.svc._current != None and self.svc._current.get_filename() == file:
            self.svc.boss.editor.cmd('show_sign', type='breakpoint', 
                                                    file_name=file,
                                                    line=line)

    def on_del_breakpoint(self, ident, file, line):
        """
        Deletes a breakpoint on line of file 
        Store it with the current controller
        """
        self.svc._controller.flush_breakpoint(ident, file, line)
        if self.svc._current != None and self.svc._current.get_filename() == file:
            self.svc.boss.editor.cmd('hide_sign', type='breakpoint', 
                                                    file_name=file, 
                                                    line=linenr)
        
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

    def prestore_breakpoint(self, file, line):
        if file not in self.get_option('prebreakpoint'):
            self.get_option('prebreakpoint')[file] = line
            return True
        return False

    _breakpoints = {}

    def init_breakpoint(self):
        if self.get_option('breakpoint') == None:
            self.set_option('breakpoint', dict())
        if self.get_option('prebreakpoint') == None:
            self.set_option('prebreakpoint', dict())

    def store_breakpoint(self, ident, file, line):
        self._breakpoints[ident] = (file, line)
#        print 'store B: ', self.get_option('breakpoint')
        if file not in self.get_option('breakpoint') \
            or line not in self.get_option('breakpoint')[file]:
                self.get_option('breakpoint')[file] = line
#        print 'store A: ', self.get_option('breakpoint')
        self.project.options.write()

    def flush_breakpoint(self, ident):
#        print 'flush B:', self.get_option('breakpoint')
        if ident in self._breakpoints:
            (file, line) = self._breakpoints[ident]
            if file in self.get_option('breakpoint'):
                if line in self.get_option('breakpoint'):
                    self.get_option('breakpoint')[file].remove(line)
#        print 'flush A:', self.get_option('breakpoint')
        self.project.options.write()

    def list_prestored_breakpoints(self):
        l = self.get_option('prebreakpoint')
#        print "lp", l
        if l == None:
            return {}
        return l

    def list_breakpoints(self):
        l = self.get_option('breakpoint')
#        print "lb", l
        if l == None:
            return {}
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
        self._current = None
        self._step = None
        self.dbg = None
        self.register_debugger('pydb', AnyDbg_pydb) # TODO: dynamic loading
        self.register_debugger('gdb', AnyDbg_gdb)   # TODO: dynamic loading

        self._breakpoints_view = AnyDbgBreakPointsView(self)
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

        if self._stack_view == None:
            self._stack_view = AnyDbgStackView(self)
#        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._stack_view)

        self.get_action('dbg_start').set_sensitive(True)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)

        self._controller.init_breakpoint()
        self.dbg.start()

        for file in self._controller.list_prestored_breakpoints():
            line = self._controller.list_prestored_breakpoints()[file]
#            print "TOG", file, line
            self.emit('toggle_breakpoint', file=file, line=line)

        for file in self._controller.list_breakpoints():
            line = self._controller.list_breakpoints()[file]
#            print "TOG", file, line
            self.emit('toggle_breakpoint', file=file, line=line)

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
            if document.get_filename() in self._controller.list_breakpoints():
                line = self._controller.list_breakpoints()[document.get_filename()]
                self.boss.editor.cmd('show_sign', type='breakpoint', 
                                                    file_name=document.get_filename(),
                                                    line=line)
        if self.dbg is not None and self._step is not None:
            (file, line) = self._step
            if file is document.get_filename():
                self.svc.boss.editor.cmd('show_sign', type='step', 
                                                        file_name=file,
                                                        line=line)

    def register_debugger(self, name, classname):
        """
        Registers a new debugger class
        """
        self._anydbg[name] = classname

# Required Service attribute for service loading
Service = Debugger

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
