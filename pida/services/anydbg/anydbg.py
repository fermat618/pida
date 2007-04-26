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

from pida.ui.views import PidaView

from pida.utils.gthreads import GeneratorTask, gcall
       
# --- TODO Stack view
class AnyDbgStackItem(object):
    def __init__(self, frame, fname, line, func, path):
        self.frame = frame
        self.fname = fname
        self.line = line
        self.func = func
        self.path = path
class AnyDbgStackView(PidaView):
    label_text = 'Stack'
    icon_name = 'accessories-text-editor'
    
    def create_ui(self):
        self.stack_list = ObjectList(
            [
                Column('Frame', sorted=True),
                Column('Filename'),
                Column('Line'),
                Column('Function'),
                Column('Path')
            ]
        )
        self.stack_list.connect('double-click', self._on_stackitem_double_click)
        self.add_main_widget(self.stack_list)
        self.stack_list.show_all()
    
    def clear_items(self):
        gcall(self._breakpoint_list.clear)
    
    def add_item(self, frame, fname, line, func, path):
        pass
#        self._breakpoint_list.append(AnyDbgItem(frame, fname, line, func, path))
    
    def _on_stackitem_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)

# --- TODO Debug console view
class AnyDbgConsoleView(PidaView):
    label_text = 'Debugger\'s console'
    icon_name = 'accessories-text-editor'

    def create_ui(self):
        pass


# --- Profile manager view

class AnyDbgProfileItem(object):
    def __init__(self, section=None):
        if section is not None:
            self.name = section['name']
            self.executable = section['executable']
            self.parameters = section['parameters']
            self.debugger = section['debugger']
            self.breakpoint_list = []
            for breakpoint in section['breakpoints']:
                self.breakpoint_list.append(eval(breakpoint))
        else:
            self.name = "Default"
            self.executable = ""
            self.parameters = ""
            self.debugger = None
            self.breakpoint_list = []

    def add_breakpoint(self,file,line):
        self.breakpoint_list.append((file,line))

    def del_breakpoint(self,file,line):
        self.breakpoint_list.remove((file,line))

    def as_dict(self):
        return dict(
            name = self.name,
            executable = self.executable,
            parameters = self.parameters,
            debugger = self.debugger,
            breakpoints = self.breakpoint_list
        )

class AnyDbgDebuggerProfile(PidaView):
    gladefile = 'anydbg-profile-editor'
    label_name = 'Debugger'
    label_text = 'New debugging profile'
    icon_name = 'accessories-text-editor'

    def create_ui(self):
        self.profile_list.set_columns([
            Column('name'),
            Column('executable'),
            Column('parameters'),
            Column('debugger')
        ])
        self._current = None
        self._block_changed = False

    def prefill(self, config):
        for section in config:
            item = AnyDbgProfileItem(config[section])
            self.profile_list.append(item)

    def set_current(self, item):
        self._current = item
        self._block_changed = True
        if item is None:
            self.name_entry.set_text('')
            self.executable_entry.set_text('')
            self.parameters_entry.set_text('')
#            self.debugger_combo.unset_?
            self.attrs_table.set_sensitive(False)
            self.delete_button.set_sensitive(False)
        else:
            self.name_entry.set_text(item.name)
            self.executable_entry.set_text(item.executable)
            self.parameters_entry.set_text(item.parameters)
#            self.debugger_combo.unset_?
            self.attrs_table.set_sensitive(True)
            self.delete_button.set_sensitive(True)
        self._block_changed = False

    def on_new_button__clicked(self, button):
        new = AnyDbgProfileItem()
        self.profile_list.append(new, select=True)
        self.save_button.set_sensitive(True)
    
    def on_save_button__clicked(self, button):
        self.svc.save_profiles([i for i in self.profile_list])
        self.save_button.set_sensitive(False)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_dbg_profile_manager').set_active(False)
        
    def on_delete_button__clicked(self, button):
        if self.svc.boss.get_window().yesno_dlg(
                'Are you sure you want to delete %s' % self._current.name):
            self.profile_list.remove(self._current, select=True)
            self.save_button.set_sensitive(True)
            
    def on_profile_list__selection_changed(self, ol, item):
        self.set_current(item)
            
    def on_name_entry__changed(self, entry):
        if not self._block_changed:
            self._current.name = entry.get_text()
            self.item_changed()
            
    def on_executable_entry__changed(self, entry):
        if not self._block_changed:
            self._current.executable = entry.get_text()
            self.item_changed()
            
    def on_parameters_entry__changed(self, entry):
        if not self._block_changed:
            self._current.parameters = entry.get_text()
            self.item_changed()

    def on_debugger_combo__changed(self, entry):
        pass
            
    def item_changed(self):
        self.save_button.set_sensitive(True)
        self.profile_list.update(self._current)

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

# --- Actions & Events

class AnyDbgActionsConfig(ActionsConfig):
    def create_actions(self):
        # Menu
        self.create_action(
            'show_breakpoints',
            TYPE_TOGGLE,
            'Debugger breakpoints list',
            'Show the breakpoints list',
            'accessories-text-editor',
            self.on_show_breakpoints,
            '<Shift><Control>d',
        )
        self.create_action(
            'show_dbg_profile_manager',
            TYPE_TOGGLE,
            'Debugger profile manager',
            'Creates a new profile for debugging',
            'accessories-text-editor',
            self.on_show_profile_manager,
            '<Shift><Control>d',
        )

        # Toolbar
        self.create_action(
            'choose_dbg_profile',
            TYPE_MENUTOOL,
            'Choose debug profile',
            'Choose a profile for debugging current project',
            'accessories-text-editor',
            self.on_choose_dbg_profile
        )

        self.create_action(
            'step_over',
            TYPE_NORMAL,
            'Step Over',
            'Step over highlighted statement',
            gtk.STOCK_MEDIA_FORWARD,
            self.svc.step_over,
            '<F6>',
        )
        self.create_action(
            'step_in',
            TYPE_NORMAL,
            'Step In',
            'Step in highlighted statement',
            gtk.STOCK_MEDIA_NEXT,
            self.svc.step_in,
            '<F5>',
        )
        self.create_action(
            'dbg_break',
            TYPE_NORMAL,
            'Break',
            'Break debbuging',
            gtk.STOCK_MEDIA_PAUSE,
            self.svc.dbg_break,
            '<F4>',
        )
        self.create_action(
            'dbg_continue',
            TYPE_NORMAL,
            'Continue',
            'Continue debbuging',
            gtk.STOCK_MEDIA_PLAY,
            self.svc.dbg_continue,
            '<F3>',
        )
        self.create_action(
            'toggle_breakpoint',
            TYPE_NORMAL,
            'Toggle breakpoint',
            'Toggle breakpoint on selected line',
            gtk.STOCK_MEDIA_RECORD,
            self.toggle_breakpoint,
            '<F3>',
        )

    def on_choose_dbg_profile(self, action):
        profile = self.svc.get_current_profile()
        if profile is None:
            profiles = [p for p in self.svc.list_profiles()]
            if profiles:
                profile = profiles[0]
        if profile is not None:
            profile.execute()
        else:
            self.svc.boss.get_window().error_dlg(
                'This project has no controllers')
        
        

    def on_show_breakpoints(self, action):
        if action.get_active():
            self.svc.show_breakpoints()
        else:
            self.svc.hide_breakpoints()

    def on_show_profile_manager(self, action):
        if action.get_active():
            self.svc.show_profile_manager()
        else:
            self.svc.hide_profile_manager()

    def toggle_breakpoint(self, action):
        self.svc.toggle_breakpoint()
        
class AnyDbgEventsConfig(EventsConfig):
    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
                                     self.on_document_changed)
        self.subscribe_foreign_event('buffer', 'document-saved',
                                     self.on_document_changed)
        self.subscribe_foreign_event('editor', 'started',
                                     self.on_editor_startup)

    def on_document_changed(self, document):
        if document != None:
            self.svc.set_current_document(document)
            self.svc.get_action("toggle_breakpoint").set_sensitive(True)
            self.svc.update_breakpoints(document)
        else:
            self.svc.get_action("toggle_breakpoint").set_sensitive(False)

    def on_editor_startup(self):
        self.svc.boss.editor.cmd('define_sign_type', type="breakpoint", icon=get_pixmap_path("stop.svg"), 
                                                linehl="", text="X", texthl="Search")
        self.svc.boss.editor.cmd('define_sign_type', type="step", icon=get_pixmap_path("forward.svg"), 
                                                linehl="lCursor", text=">", texthl="lCursor")


# Service class
class Debugger(Service):
    """Debugging a project service""" 

    actions_config = AnyDbgActionsConfig
    events_config = AnyDbgEventsConfig

    def start(self):
        self._current = None
        self._stepcursor_position=0

        self._filename = os.path.join(self.boss.get_pida_home(), 'debugger-profiles.ini')
        self._config = ConfigObj(self._filename)
        self._profile_manager=AnyDbgDebuggerProfile(self)
        self._profile_manager.prefill(self._config)
        self._current_profile = None

        self._breakpoints_view = AnyDbgBreakPointsView(self)

        self.get_action("step_in").set_sensitive(False)
#        self.get_action("step_over").set_sensitive(False)
        self.get_action("dbg_continue").set_sensitive(False)
        self.get_action("dbg_break").set_sensitive(False)
        self.get_action("toggle_breakpoint").set_sensitive(False)

        self.select_profile(None)

#    def show_backtrace(self):
#    def hide_backtrace(self):
#    def show_variables(self):
#    def hide_variables(self):
#    def show_console(self):
#    def hide_console(self):

    def show_breakpoints(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._breakpoints_view)

    def hide_breakpoints(self):
        self.boss.cmd('window','remove_view', view=self._breakpoints_view)

    def toggle_breakpoint(self):
        if not self.add_breakpoint(self._current.get_filename(),
                        self.boss.editor.cmd('get_current_line_number')):
            if not self.del_breakpoint(self._current.get_filename(),
                            self.boss.editor.cmd('get_current_line_number')):
                self.window.error_dlg('Tried to remove non-existing breakpoint')

    def add_breakpoint(self,file,linenr):
        if self._add_breakpoint(file,linenr):
            self._current_profile.add_breakpoint(file, linenr)
            self._config[self._current_profile.name] = self._current_profile.as_dict()
            self._config.write()
           
            return True
        return False

    def del_breakpoint(self,file,linenr):
        if self._del_breakpoint(file,linenr):
            self._current_profile.del_breakpoint(file, linenr)
            self._config[self._current_profile.name] = self._current_profile.as_dict()
            self._config.write()
            return True
        return False

    def _add_breakpoint(self,file,linenr):
        if self._breakpoints_view.add_breakpoint(file,linenr):
#            self._dbg.add_breakpoint(file,linenr)
            self.boss.editor.cmd('show_sign', type='breakpoint', file_name=file, line=linenr)
            return True
        else:
            return False

    def _del_breakpoint(self,file,linenr):
        if self._breakpoints_view.del_breakpoint(file,linenr):
#            self._dbg.del_breakpoint(file,linenr)
            self.boss.editor.cmd('hide_sign', type='breakpoint', file_name=file, line=linenr)
            return True
        else:
            return False

    def show_profile_manager(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._profile_manager)

    def save_profiles(self, items):
        self._config.clear()
        for item in items:
            self._config[item.name] = item.as_dict()
            self._config.write()

    def list_profiles(self):
        if len(self._config) == 0:
            yield AnyDbgProfileItem()
        for profile in self._config:
            item = AnyDbgProfileItem(self._config[profile])
            yield item

    def select_profile(self, profile):
#        self._breakpoints_view.clear_items()

#        print "DEBUG: anydbg: select_profile(): profile: ", profile 
#        if self._current_profile != None:
#            print "DEBUG: anydbg: select_profile(): current profile: ", self._current_profile.as_dict()

        if profile in self._config:
            self._current_profile = AnyDbgProfileItem(self._config[profile])
#            self.emit('debug_profile_switched', profile=profile)
        else:
            self._current_profile = self.list_profiles().next()
        toolitem = self.get_action('choose_dbg_profile').get_proxies()[0]
        toolitem.set_menu(self.create_menu())
        self.reset_breakpoints()

    def update_breakpoints(self, document):
        if self._current_profile.breakpoint_list != []:
            for (file, line) in self._current_profile.breakpoint_list:
                if document.get_filename() == file:
                    self.boss.editor.cmd('show_sign', type='breakpoint', file_name=file, line=line)

    def reset_breakpoints(self):
        bplist = dict(self._breakpoints_view.get_breakpoint_list())
        for (file, line) in bplist:
            self._del_breakpoint(file,line)
        for (file, line) in self._current_profile.breakpoint_list:
#            print "DEBUG: anydbg: reset_breakpoints(): adding new breakpoint:", (file, line)
            self._add_breakpoint(file,line)

    def hide_profile_manager(self):
        self.boss.cmd('window', 'remove_view', view=self._profile_manager)
        
    def step_over(self,action):
        if self._stepcursor_position != 0:
            self.boss.editor.cmd('hide_sign', type='step', file_name=self._current.get_filename(), line=self._stepcursor_position)
        self._stepcursor_position = self._stepcursor_position+1
        self.boss.editor.cmd('show_sign', type='step', file_name=self._current.get_filename(), line=self._stepcursor_position)

    def step_in(self):
        self.boss.editor.cmd('hide_sign', type='step', file_name=self._current.get_filename(), line=self._stepcursor_position)
        self._stepcursor_position = self._stepcursor_position+1
        self.boss.editor.cmd('show_sign', type='step', file_name=self._current.get_filename(), line=self._stepcursor_position)

    def dbg_break(self):
        pass

    def dbg_continue(self):
        pass

    def set_current_document(self, document):
        self._current = document

    def get_current_profile(self):
        return self._current_profile

    def create_menu(self):
        if self._current_profile is not None:
            menu = gtk.Menu()
            for profile in self.list_profiles():
                def _callback(act, profile):
                    self.select_profile(profile.name)
                act = gtk.Action(profile.name,
                    profile.name,
                    profile.executable, gtk.STOCK_EXECUTE)
                act.connect('activate', _callback, profile)
                mi = act.create_menu_item()
                menu.add(mi)
            menu.show_all()
            return menu

# Required Service attribute for service loading
Service = Debugger



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
