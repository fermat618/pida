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

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.options import OTypeString, OTypeFile
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE
from pida.core.environment import get_pixmap_path
from pida.core.projects import ProjectController, \
    ProjectKeyDefinition
from pida.core.interfaces import IProjectController

from pida.utils.debugger.views import DebuggerBreakPointsView, DebuggerStackView

# Actions
class DebuggerActionsConfig(ActionsConfig):
    def create_actions(self):
        # Menu
        self.create_action(
            'debug_show_breakpoints_view',
            TYPE_TOGGLE,
            'Debugger breakpoints list',
            'Show the breakpoints list',
            'accessories-text-editor',
            self.on_show_breakpoints_view,
            '<Shift><Control>b',
        )
        self.create_action(
            'debug_show_stack_view',
            TYPE_TOGGLE,
            "Debugger's stack view",
            'Show the stack of current debugger',
            'accessories-text-editor',
            self.on_show_stack_view,
            '<Shift><Control>s',
        )
    
        # Toolbar
        self.create_action(
            'debug_start',
            TYPE_NORMAL,
            'Continue',
            'Start debugger or Continue debbuging',
            'gdb-go',
            self.on_start,
            '<F3>',
        )
        self.create_action(
            'debug_stop',
            TYPE_NORMAL,
            'Break',
            'Stop debbuging',
            'gdb-break',
            self.on_stop,
            '<F4>',
        )
        self.create_action(
            'debug_next',
            TYPE_NORMAL,
            'Step Over',
            'Step over highlighted statement',
            'gdb-next',
            self.on_step_over,
            '<F6>',
        )
        self.create_action(
            'debug_step',
            TYPE_NORMAL,
            'Step In',
            'Step in highlighted statement',
            'gdb-step',
            self.on_step_in,
            '<F5>',
        )
        self.create_action(
            'debug_return',
            TYPE_NORMAL,
            'Finish function',
            'Step until end of current function',
            'gdb-return',
            self.on_return,
            '<F7>',
        )
        self.create_action(
            'debug_toggle_breakpoint',
            TYPE_NORMAL,
            'Toggle breakpoint',
            'Toggle breakpoint on selected line',
            'gdb-toggle-bp',
            self.on_toggle_breakpoint,
            '<F3>',
        )

    # Buttonbar
    def on_step_over(self, action):
        self.svc.step_over()

    def on_step_in(self, action):
        self.svc.step_in()

    def on_start(self, action):
        self.svc.start()

    def on_stop(self, action):
        self.svc.stop()

    def on_return(self, action):
        self.svc.finish()

    # Menu
    def on_show_breakpoints_view(self, action):
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._breakpoints_view)

    def on_show_stack_view(self, action):
        if not self.svc._stack_view:
            self.svc._stack_view = DebuggerStackView(self.svc)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._stack_view)
        
    #
    def on_toggle_breakpoint(self, action):
        self.svc.emit('toggle_breakpoint', file=self.svc._current.get_filename(),
                        line=self.svc.boss.editor.cmd('get_current_line_number'))

# Events
class DebuggerEventsConfig(EventsConfig):
    def create_events(self):
        # UI events
        self.create_event('toggle_breakpoint')

        # Debugger events
        self.create_event('debugger_started')
        self.create_event('reset')
        self.create_event('step')
        self.create_event('thread')
        self.create_event('function_call')
        self.create_event('function_return')
        self.create_event('add_breakpoint')
        self.create_event('del_breakpoint')
        self.create_event('debugger_ended')

        self.subscribe_event('toggle_breakpoint', self.on_toggle_breakpoint)
        self.subscribe_event('add_breakpoint', self.on_add_breakpoint)
        self.subscribe_event('debugger_started', self.on_start_debugging)

        self.subscribe_event('step', self.on_step)

    def on_step(self, file, line, function):
        self.svc.boss.cmd('buffer', 'open_file', file_name=file)

        if self.svc._current is not None and file == self.svc._current.get_filename():
            for (oldfile, oldline) in self.svc._step:
                if oldfile == self.svc._current.get_filename():
                    self.svc.boss.editor.cmd('hide_sign', type='step', 
                                                            file_name=oldfile,
                                                            line=oldline)
                    self.svc._step.remove((oldfile, oldline))

            self.svc.boss.editor.cmd('goto_line', line=line)
            self.svc.boss.editor.cmd('show_sign', type='step', 
                                                    file_name=file,
                                                    line=line)
            self.svc._step.append((file, line))

    def on_toggle_breakpoint(self, file, line):
        """
        Toggles a breakpoint on line of file
        Store the breakpoint and mark it as unverified
        """
        raise NotImplementedError

    def on_add_breakpoint(self, ident, file, line):
        """
        Add a breakpoint on line of file
        Store it with the current controller
        """
        raise NotImplementedError

    def on_del_breakpoint(self, ident):
        """
        Deletes a breakpoint on line of file 
        Store it with the current controller
        """
        raise NotImplementedError

    def on_start_debugging(self):
        self.svc.get_action('debug_start').set_sensitive(True)
        self.svc.get_action('debug_stop').set_sensitive(True)
        self.svc.get_action('debug_return').set_sensitive(True)
        self.svc.get_action('debug_step').set_sensitive(True)
        self.svc.get_action('debug_next').set_sensitive(True)

        self.svc._init()

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
                                     self.on_document_changed)
        self.subscribe_foreign_event('editor', 'started',
                                     self.on_editor_startup)

    def on_editor_startup(self):
        """
        Set the highlights in vim
        """
        self.svc.boss.editor.cmd('define_sign_type', type="breakpoint", icon=get_pixmap_path("stop.svg"), 
                                                linehl="", text="X", texthl="Search")
        self.svc.boss.editor.cmd('define_sign_type', type="step", icon=get_pixmap_path("forward.svg"), 
                                                linehl="lCursor", text=">", texthl="lCursor")

    def on_document_changed(self, document):
        if document is not None:
            self.svc.get_action('debug_toggle_breakpoint').set_sensitive(True)
            self.svc.update_editor(document)
        else:
            self.svc.get_action('debug_toggle_breakpoint').set_sensitive(False)

# Controller
class GenericDebuggerController(ProjectController):
    name = 'GENERIC_DEBUGGER'

    label = 'Generic Debugger'

    svcname = ''

    debugger = None

    # parameters of the debugger

    attributes = [
        ProjectKeyDefinition('executable', 'Path to the executable', True),
        ProjectKeyDefinition('parameters', 'Parameters to give to the executable', True),
    ] + ProjectController.attributes

    def execute(self):
        """
        Execute debugger
        """
        self.svc = self.boss.get_service(self.svcname)
        self.svc._executable = self.get_option('executable')
        self.svc._parameters = self.get_option('parameters')
        self.svc._controller = self

        if not self.svc._executable:
            self.boss.get_window().error_dlg(
                'Debug controller is not fully configured.')
        else:

            if self.svc.init():
                self.svc.emit('debugger_started')
            else:
                self.boss.get_window().error_dlg(
                    'Debug session failed to launch.')

    # breakpoint recording management
    _breakpoints = {}

    def init_breakpoint(self):
        """
        init breakpoint storage
        """
        if self.get_option('breakpoint') is None:
            self.set_option('breakpoint', dict())

    def store_breakpoint(self, ident, file, line):
        """
        Store breakpoint
        """
        self._breakpoints[ident] = (file, line)
        if file not in self.get_option('breakpoint') \
            or line not in self.get_option('breakpoint')[file]:
                self.get_option('breakpoint')[file] = line
        self.project.options.write()
        l = self.get_option('breakpoint')

    def flush_breakpoint(self, ident):
        """
        Remove breakpoint from recorded list
        """
        if ident in self._breakpoints:
            (file, line) = self._breakpoints[ident]
            if file in self.get_option('breakpoint'):
                if line in self.get_option('breakpoint'):
                    self.get_option('breakpoint')[file].remove(line)
        self.project.options.write()
        l = self.get_option('breakpoint')

    def list_breakpoints(self):
        l = self.get_option('breakpoint')
        if l is None:
            return {}
        return l
        
class DebuggerFeaturesConfig(FeaturesConfig):
    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController, 
                                                    self.svc.controller_config)

class DebuggerOptionsConfig(OptionsConfig):
    name = 'debugger'
    def create_options(self):
        self.create_option(
            self.name+'breakpoint_pixmap',
            "Breakpoint's pixmap",
            OTypeFile,
            get_pixmap_path("stop.svg"),
            'Path to a pixmap for the breakpoints to be displayed at \
beginning of line',
        )
        self.create_option(
            self.name+'_cursor_pixmap',
            "Debugging cursor's pixmap",
            OTypeFile,
            get_pixmap_path("forward.svg"),
            'Path to a pixmap for the cursor to be displayed at \
beginning of line where debugger is halted')

        self.create_option(
            self.name+'_executable_path',
            'Pathes to the GDB-compatible debugger : ',
            OTypeString,
            self.svc.DEFAULT_DEBUGGER_PATH_OPTION,
            ('Set the path to the debugger executable.')
        )

# Service class
class Debugger(Service):
    """Debugging a project service""" 

    DEFAULT_DEBUGGER_PATH_OPTION = None

    actions_config = DebuggerActionsConfig
    events_config = DebuggerEventsConfig
    features_config = DebuggerFeaturesConfig
    options_config = DebuggerOptionsConfig

    controller_config = GenericDebuggerController

    __breakpoints = {}

    def _store_breakpoint_toggle(self, file, line, init=False):
        """
        When a new or clear breakpoint event happens, this is called
        I don't care whether this is a correct or wrong breakpoint.
        """
        if file not in self.__breakpoints:
            self.__breakpoints[file] = [line]
        else:
            self.__breakpoints[file].append(line)

    def _list_breakpoints(self, file=None):
        """
        Lists all breakpoints choosed by the user
        """
        try:
            l = self.get_option('breakpoint')
            if l is not None:
                self.__breakpoints = self.__breakpoints + l
        except KeyError, ke:
            print "Breakpoints records not found (", ke, ")"

        if file is not None:
            for line in self.__breakpoints[file]:
                yield (file, line)
        else:
            for f in self.__breakpoints:
                for line in self.__breakpoints[file]:
                    yield (f, line)

    def _load_breakpoints(self):
        """
        Load all breakpoints in the debugger
        """
        self.__bp_init = True
        for (file, line) in self._list_breakpoints():
            self.emit('toggle_breakpoint', file=file, line=line)
        self.__bp_init = False
        self.__breakpoints = {}

    def start(self):
        """
        Starts the service
        """
        self._step = []
        self._current = None
        self._is_running = False

        # initiate the views
        self._breakpoints_view = DebuggerBreakPointsView(self)
        self._stack_view = DebuggerStackView(self)

        # Sets default sensitivity for button bar
        self.get_action('debug_step').set_sensitive(False)
        self.get_action('debug_next').set_sensitive(False)
        self.get_action('debug_return').set_sensitive(False)
        self.get_action('debug_start').set_sensitive(False)
        self.get_action('debug_stop').set_sensitive(False)
        self.get_action('debug_toggle_breakpoint').set_sensitive(False)

        # load cached breakpoints
        self._load_breakpoints()

    def update_editor(self, document):
        """
        Updates the editor with current's document breakpoints
        """
        # update the editor
        self._current = document
        if self._controller is not None:
            if document.get_filename() in self._controller.list_breakpoints():
                line = self._list_breakpoints(document.get_filename())
                self.boss.editor.cmd('show_sign', type='breakpoint', 
                                                    file_name=document.get_filename(),
                                                    line=line)
        if self._is_running is not None and self._step != []:
            (file, line) = self._step[-1]
            if file is document.get_filename():
                self.boss.editor.cmd('show_sign', type='step', 
                                                    file_name=file,
                                                    line=line)

    def _init(self):
        self._is_running = True
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._stack_view)
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._breakpoints_view)

    def _end(self):
        self._is_running = False

        self.get_action('debug_start').set_sensitive(False)
        self.get_action('debug_stop').set_sensitive(False)
        self.get_action('debug_step_in').set_sensitive(False)
        self.get_action('debug_step_over').set_sensitive(False)
        self.get_action('debug_return').set_sensitive(False)

        # removing old cursor
        for (oldfile, oldline) in self._step:
            self.boss.editor.cmd('hide_sign', type='step', 
                                                    file_name=oldfile,
                                                    line=oldline)
            self._step.remove((oldfile, oldline))

        return self.end()

    # abstract interface to be implemented by services
    def init(self, executable, parameters, controller):
        """
        Initiates the debugging session
        """
        raise NotImplementedError

    def end(self):
        """
        Ends the debugging session
        """
        raise NotImplementedError

    def step_in(self):
        """
        step in instruction
        """
        raise NotImplementedError
        
    def step_over(self):
        """
        Step over instruction
        """
        raise NotImplementedError

    def cont(self):
        """
        Continue execution
        """
        raise NotImplementedError

    def finish(self):
        """
        Finish current function call
        """
        raise NotImplementedError

# Required Service attribute for service loading
Service = Debugger

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
