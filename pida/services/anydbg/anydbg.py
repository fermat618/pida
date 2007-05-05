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

from kiwi.ui.objectlist import ObjectTree, ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.options import OTypeStringList, OTypeFile
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE
from pida.core.environment import get_pixmap_path, get_uidef_path
from pida.core.interfaces import IProjectController
from pida.core.projects import ProjectController, \
    ProjectKeyDefinition

from pida.ui.views import PidaView
from pida.ui.buttons import create_mini_button

from pida.utils.gthreads import GeneratorTask, gcall

from pida.utils.anydbg import AnyDbg

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
        self._prebreakpoints = {}
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
            for file in self.svc._controller.list_breakpoints():
                line = self.svc._controller.list_breakpoints()[file]
                self.add_breakpoint(None, file, line)

        self.svc.subscribe_event('add_breakpoint', self.add_breakpoint)
        self.svc.subscribe_event('del_breakpoint', self.del_breakpoint)

    def clear_items(self):
        gcall(self._breakpoint_list.clear)

    def toggle_breakpoint(self, file, line):
        breakpoint = AnyDbgBreakPointItem(file, line, 'disabled')

        if (file, line) not in self._prebreakpoints:
            self._prebreakpoints[(file,line)] = breakpoint
            self._breakpoint_list.append(breakpoint)
        else:
            oldbp = self._prebreakpoints.pop((file,line))
            self._breakpoint_list.remove(oldbp)

    def add_breakpoint(self, ident, file, line):

        if (file, int(line)) in self._prebreakpoints:
            breakpoint = self._prebreakpoints.pop((file, int(line)))
            breakpoint.status = 'enabled'
            self._breakpoint_list.remove(breakpoint)
        else:
            breakpoint = AnyDbgBreakPointItem(file, int(line))

        if ident not in self._breakpoints:
            self._breakpoints[ident] = breakpoint
            self._breakpoint_list.append(breakpoint)
            return True
        else:
            return False
    
    def del_breakpoint(self, ident):
        if ident in self._breakpoints:
            self._breakpoint_list.remove(self._breakpoints[ident])
            del(self._breakpoints[ident])
            return True
        else:
            return False

    def get_breakpoint_list(self):
        return self._breakpoints
    
    def _on_breakpoint_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.file)


# --- Function stack view

class AnyDbgStackItem(object):
    def __init__(self, frame, function, file, line):
        self.thread = ""
        self.frame = frame
        self.function = function
        self.file = file
        self.line = line
        self.parent = None

class AnyDbgStackThreadItem(object):
    def __init__(self,thread):
        self.thread = thread
        self.frame = ""
        self.function = ""
        self.file = ""
        self.line = ""
        self.parent = None

class AnyDbgStackView(PidaView):
    label_text = 'Debug Function Stack'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self.__last = None
        self.__call = False
        self.__return = False
        self.__cnt = 0

        # Toolbar
        self.create_toolbar()

        # Tree
        self._stack_list = ObjectTree(
            [
                Column('thread'), 
                Column('frame'), 
                Column('line'),
                Column('function'),
                Column('file'),
            ]
        )
        self._stack_list.connect('double-click', self._on_frame_double_click)

        # Arrange the UI
        self._vbox = gtk.VBox()
        self._vbox.pack_start(self._toolbar, expand=False)
        self._vbox.pack_start(self._stack_list, expand=True)
        self.add_main_widget(self._vbox)
        self._vbox.show_all()

        self.svc.subscribe_event('function_call', self.on_function_call)
        self.svc.subscribe_event('function_return', self.on_function_return)
        self.svc.subscribe_event('step', self.on_step)
        self.svc.subscribe_event('thread', self.on_thread_stmt)

        self._thread = { None:None }
        self.__current_thread = None

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_file(get_uidef_path('stackview-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._toolbar.show_all()

    def on_thread_stmt(self, thread):
        self.__current_thread = thread

        thread_item = AnyDbgStackThreadItem(thread)
        if thread not in self._thread:
            self._thread[thread] = thread_item
            self._stack_list.prepend(None, thread_item)

    def on_function_call(self):
        self.__call = True

    def on_function_return(self):
        self.__return = True

    def on_step(self, file, line, function):
        if self.__return is True:
            self.pop_function()
            self.__return = False

        if self.__call is True:
            self.push_function(function, file, line, self.__current_thread)
            self.__call = False

        if self.__call is False and self.__return is False:
            if self.__last is None:
                self.push_function(function, file, line, self.__current_thread)
            else:
                self.pop_function()
                self.push_function(function, file, line, self.__current_thread)

        return True

    def clear_items(self):
        gcall(self._breakpoint_list.clear)

    def push_function(self, function, file, line, thread=None):
        self.__cnt = self.__cnt + 1
        func = AnyDbgStackItem(self.__cnt, function, file, line)
        func.parent = self.__last
        self._stack_list.prepend(self._thread[thread],func)
        self.__last = func
    
    def pop_function(self):
        if self.__last is not None:
            self._stack_list.remove(self.__last)
            self.__last = self.__last.parent
        self.__cnt = self.__cnt - 1

    def _on_frame_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.file)

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
            'gdb-go',
            self.on_start,
            '<F3>',
        )
        self.create_action(
            'dbg_stop',
            TYPE_NORMAL,
            'Break',
            'Stop debbuging',
            'gdb-break',
            self.on_stop,
            '<F4>',
        )
        self.create_action(
            'step_over',
            TYPE_NORMAL,
            'Step Over',
            'Step over highlighted statement',
            'gdb-next',
            self.on_step_over,
            '<F6>',
        )
        self.create_action(
            'step_in',
            TYPE_NORMAL,
            'Step In',
            'Step in highlighted statement',
            'gdb-step',
            self.on_step_in,
            '<F5>',
        )
        self.create_action(
            'return',
            TYPE_NORMAL,
            'Finish function',
            'Step until end of current function',
            'gdb-return',
            self.on_return,
            '<F7>',
        )
        self.create_action(
            'toggle_breakpoint',
            TYPE_NORMAL,
            'Toggle breakpoint',
            'Toggle breakpoint on selected line',
            'gdb-toggle-bp',
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

    def on_return(self, action):
        self.svc.dbg.finish()

    # Menu
    def on_show_breakpoints_view(self, action):
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._breakpoints_view)

    def on_show_stack_view(self, action):
        if not self.svc._stack_view:
            self.svc._stack_view = AnyDbgStackView(self.svc)
        self.svc.boss.cmd('window', 'add_view', paned='Plugin', view=self.svc._stack_view)
        
    def on_show_console_view(self, action):
        if self.svc.dbg is not None:
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
        self.create_event('thread')
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
        if self.svc.dbg is not None:
            self.svc.dbg.toggle_breakpoint(file, line)
        else:
            self.svc.prestore_breakpoint(file, line)
            self.svc._breakpoints_view.toggle_breakpoint(file, line)

    def on_add_breakpoint(self, ident, file, line):
        """
        Add a breakpoint on line of file
        Store it with the current controller
        """
        if self.svc._controller is not None:
            self.svc._controller.store_breakpoint(ident, file, line)
        if self.svc._current is not None and file is self.svc._current.get_filename():
            self.svc.boss.editor.cmd('show_sign', type='breakpoint', 
                                                    file_name=file,
                                                    line=line)

    def on_del_breakpoint(self, ident):
        """
        Deletes a breakpoint on line of file 
        Store it with the current controller
        """
        if self.svc._controller is not None:
            self.svc._controller.flush_breakpoint(ident)
        if self.svc._current is not None and file == self.svc._current.get_filename():
            self.svc.boss.editor.cmd('hide_sign', type='breakpoint', 
                                                    file_name=file, 
                                                    line=linenr)
        
    def on_start_debugging(self, executable, arguments):
        self.svc.get_action('step_in').set_sensitive(True)
        self.svc.get_action('step_over').set_sensitive(True)
        self.svc.get_action('return').set_sensitive(True)
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
        """
        self.svc.boss.editor.cmd('define_sign_type', type="breakpoint", icon=get_pixmap_path("stop.svg"), 
                                                linehl="", text="X", texthl="Search")
        self.svc.boss.editor.cmd('define_sign_type', type="step", icon=get_pixmap_path("forward.svg"), 
                                                linehl="lCursor", text=">", texthl="lCursor")

    def on_document_changed(self, document):
        if document is not None:
            self.svc.get_action('toggle_breakpoint').set_sensitive(True)
            self.svc.update_editor(document)
        else:
            self.svc.get_action('toggle_breakpoint').set_sensitive(False)

# Controller
class GenericDebuggerController(ProjectController):
    name = 'GENERIC_DEBUGGER'

    label = 'Generic Debugger'

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
        executable = self.get_option('executable')
        parameters = self.get_option('parameters')
        if not self.debugger or not executable:
            self.boss.get_window().error_dlg(
                'Debug controller is not fully configured.' 
            )
        else:
            self.boss.get_service('anydbg').emit('launch_debugger',
                                                 executable=executable,
                                                 parameters=parameters,
                                                 debugger=self.debugger,
                                                 controller=self)

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
        
class AnyDbgFeaturesConfig(FeaturesConfig):
    def subscribe_foreign_features(self):
        for path in self.svc.opt('gdb_executable_path'):
            ctler = self.svc.register_debugger(path.split('/')[-1], AnyDbg('gdb'), path=path)
            self.subscribe_foreign_feature('project', IProjectController, ctler)

class AnyDbgOptionsConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
            'breakpoint_pixmap',
            "Breakpoint's pixmap",
            OTypeFile,
            get_pixmap_path("stop.svg"),
            'Path to a pixmap for the breakpoints to be displayed at \
beginning of line',
        )
        self.create_option(
            'cursor_pixmap',
            "Debugging cursor's pixmap",
            OTypeFile,
            get_pixmap_path("forward.svg"),
            'Path to a pixmap for the cursor to be displayed at \
beginning of line where debugger is halted')

        self.create_option(
            'gdb_executable_path',
            'Pathes to GDB-compatible debuggers :',
            OTypeStringList,
            ['/usr/bin/pydb',
             '/usr/bin/bashdb',
             '/usr/bin/gdb'],
            ("Add or remove the path to any debugger whose console has the \
same interface as gdb's.")
        )

# Service class
class Debugger(Service):
    """Debugging a project service""" 

    actions_config = AnyDbgActionsConfig
    events_config = AnyDbgEventsConfig
    features_config = AnyDbgFeaturesConfig
    options_config = AnyDbgOptionsConfig

    _anydbg = {}
    _anydbg_param = {}

    def start(self):
        """
        Starts the service
        """

        self._controller = None
        self._current = None
        self._step = []

        self.__prestored_bp = {}

        self.dbg = None

        self._breakpoints_view = AnyDbgBreakPointsView(self)
        self._stack_view = None

        # Sets default sensitivity for button bar
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)
        self.get_action('return').set_sensitive(False)
        self.get_action('dbg_start').set_sensitive(False)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('toggle_breakpoint').set_sensitive(False)

    def init_dbg_session(self, executable, parameters, debugger, controller):
        """
        Initiates the debugging session
        """
        self.dbg = self._anydbg[debugger](executable, 
                                            parameters, 
                                            self,
                                            self._anydbg_param[debugger])
        self._controller = controller

        if self._stack_view is None:
            self._stack_view = AnyDbgStackView(self)
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._stack_view)

        self.get_action('dbg_start').set_sensitive(True)
        self.get_action('dbg_stop').set_sensitive(False)
        self.get_action('return').set_sensitive(False)
        self.get_action('step_in').set_sensitive(False)
        self.get_action('step_over').set_sensitive(False)

        self._controller.init_breakpoint()
        self.dbg.start()

        for (file, line) in self.prestore_breakpoint_list():
            self.emit('toggle_breakpoint', file=file, line=line)
        self.prestore_breakpoint_flush()

        for file in self._controller.list_breakpoints():
            for line in self._controller.list_breakpoints()[file]:
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
        self.get_action('return').set_sensitive(False)

        # removing old cursor
        for (oldfile, oldline) in self._step:
            self.boss.editor.cmd('hide_sign', type='step', 
                                                    file_name=oldfile,
                                                    line=oldline)
            self._step.remove((oldfile, oldline))

    def prestore_breakpoint(self, file, line):
        if file not in self.__prestored_bp:
            self.__prestored_bp[file] = [line]
        else:
            if line in self.__prestored_bp[file]:
                self.__prestored_bp[file].remove(line)
            else:
                self.__prestored_bp[file].append(line)

    def prestore_breakpoint_list(self):
        for file in self.__prestored_bp:
            for line in self.__prestored_bp[file]:
                yield (file, line)

    def prestore_breakpoint_flush(self):
        self.__prestored_bp = {}

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
        if self.dbg is not None and self._step != []:
            (file, line) = self._step[-1]
            if file is document.get_filename():
                self.boss.editor.cmd('show_sign', type='step', 
                                                    file_name=file,
                                                    line=line)

    def register_debugger(self, name, classname, **kargs):
        """
        Registers a new debugger class
        """
        self._anydbg[name] = classname
        self._anydbg_param[name] = kargs

        members = dict(vars(GenericDebuggerController))
        members['name'] = name.upper()+'_DEBUGGER'
        members['label'] = name + ' debugger'
        members['debugger'] = name

        return type(name+'_DbgController', 
                    (GenericDebuggerController,),
                    members)

# Required Service attribute for service loading
Service = Debugger

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
