# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import pkgutil
import gtk

from pygtkhelpers.ui.objectlist import ObjectTree, ObjectList, Column

# PIDA Imports
from pida.utils.gthreads import gcall

from pida.ui.views import PidaView

# --- Breakpoint list view

class DebuggerBreakPointItem(object):
    def __init__(self, file, line, status='enabled'):
        self.file = file
        self.line = line
        self.status = status

class DebuggerBreakPointsView(PidaView):
    label_text = 'Debug Breakpoints'
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self._prebreakpoints = {}
        self._breakpoints = {}
        self._breakpoint_list = ObjectList([
                Column('line'),
                Column('file', sorted=True),
                Column('status')
        ])
        self._breakpoint_list.connect('item-activated', self._on_breakpoint_double_click)
        self.add_main_widget(self._breakpoint_list)
        self._breakpoint_list.show_all()

        for (file, line) in self.svc._list_breakpoints():
            self.add_breakpoint(None, file, line)

        self.svc.subscribe_event('add_breakpoint', self.add_breakpoint)
        self.svc.subscribe_event('del_breakpoint', self.del_breakpoint)
        self.svc.subscribe_event('toggle_breakpoint', self.toggle_breakpoint)
        self.svc.subscribe_event('debugger_started', self.start_debug_session)
        self.svc.subscribe_event('debugger_ended', self.end_debug_session)

    def start_debug_session(self):
        pass

    def end_debug_session(self):
        self._prebreakpoints = self._breakpoints
        self._breakpoints = {}
        for item in self._breakpoint_list:
            if item.status == 'disabled':
                self._breakpoint_list.remove(item)
            else:
                item.status = 'disabled'

    def clear_items(self):
        self._prebreakpoints = {}
        self._breakpoints = {}
        gcall(self._breakpoint_list.clear)

    def toggle_breakpoint(self, file, line):
        if self.svc._is_running:
            return

        breakpoint = DebuggerBreakPointItem(file, line, 'disabled')

        if (file, line) not in self._prebreakpoints:
            self._prebreakpoints[(file,line)] = breakpoint
            self._breakpoint_list.append(breakpoint)
        else:
            oldbp = self._prebreakpoints.pop((file,line))
            self._breakpoint_list.remove(oldbp)

    def add_breakpoint(self, ident, file, line):
#        print 'view.add_breakpoint', ident, file, line

        if (file, int(line)) in self._prebreakpoints:
            breakpoint = self._prebreakpoints.pop((file, int(line)))
            breakpoint.status = 'enabled'
            self._breakpoint_list.remove(breakpoint)
        else:
            breakpoint = DebuggerBreakPointItem(file, int(line))

        if ident not in self._breakpoints:
            self._breakpoints[ident] = breakpoint
            self._breakpoint_list.append(breakpoint)
            return True
        else:
            return False
    
    def del_breakpoint(self, ident):
#        print 'view.del_breakpoint', ident

        if ident in self._breakpoints:
            self._breakpoint_list.remove(self._breakpoints[ident])
            del(self._breakpoints[ident])
            return True
        else:
            return False

    def get_breakpoint_list(self):
#        print 'view.get_breakpoint_list'
        return self._breakpoints
    
    def _on_breakpoint_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.file)

    def can_be_closed(self):
        self.svc.get_action('debug_show_breakpoints_view').set_active(False)
        return True

# --- Function stack view

class DebuggerStackItem(object):
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

class DebuggerStackView(PidaView):
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
        self._stack_list = ObjectTree([
            Column('thread'),
            Column('frame'),
            Column('line'),
            Column('function'),
            Column('file'),
        ])
        self._stack_list.connect('item-activated', self._on_frame_double_click)

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
        self.svc.subscribe_event('debugger_ended', self.end_debug_session)

        self._thread = { None:None }
        self.__current_thread = None

    def end_debug_session(self):
        self.clear_items()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        uidef_data = pkgutil.get_data(__name__,
                'debugger_stackview_toolbar.xml')
        self._uim.add_ui_from_string(uidef_data)
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
        self.__last = None
        self.__call = False
        self.__return = False
        self.__cnt = 0
        self._thread = { None:None }
        self.__current_thread = None
        gcall(self._stack_list.clear)

    def push_function(self, function, file, line, thread=None):
        self.__cnt = self.__cnt + 1
        func = DebuggerStackItem(self.__cnt, function, file, line)
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

    def can_be_closed(self):
        self.svc.get_action('debug_show_stack_view').set_active(False)
        return True

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
