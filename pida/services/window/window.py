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

import gtk
import string

# PIDA Imports
from pida.core.service import Service
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, Color
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE
from pida.core.document import Document
from pida.core.environment import session_name

# locale
from pida.core.locale import Locale
locale = Locale('window')
_ = locale.gettext


class WindowCommandsConfig(CommandsConfig):

    def add_view(self, paned, view, removable=True, present=True):
        self.svc.window.add_view(paned, view, removable, present)

    def add_detached_view(self, paned, view, size=(500,400)):
        self.add_view(paned, view)
        self.detach_view(view, size)

    def remove_view(self, view):
        self.svc.window.remove_view(view)

    def detach_view(self, view, size):
        self.svc.window.detach_view(view, size)

    def present_view(self, view):
        self.svc.window.present_view(view)

class WindowActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_toolbar',
            TYPE_TOGGLE,
            _('Show Toolbar'),
            _('Toggle the visible state of the toolbar'),
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>l',
        )

        self.create_action(
            'show_menubar',
            TYPE_TOGGLE,
            _('Show Menubar'),
            _('Toggle the visible state of the menubar'),
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>u',
        )

        self.create_action(
            'switch_next_term',
            TYPE_NORMAL,
            _('Next terminal'),
            _('Switch to the next terminal'),
            gtk.STOCK_GO_FORWARD,
            self.on_switch_next_term,
            '<Alt>Right',
        )

        self.create_action(
            'switch_prev_term',
            TYPE_NORMAL,
            _('Previous terminal'),
            _('Switch to the previous terminal'),
            gtk.STOCK_GO_BACK,
            self.on_switch_prev_term,
            '<Alt>Left',
        )

        self.create_action(
            'focus_terminal',
            TYPE_NORMAL,
            _('Focus terminal'),
            _('Focus terminal pane terminal'),
            'terminal',
            self.on_focus_terminal,
            '<Shift><Control>i',
        )

    def on_focus_terminal(self, action):
        self.svc.window.present_paned('Terminal')

    def on_switch_next_term(self, action):
        self.svc.window.switch_next_view('Terminal')

    def on_switch_prev_term(self, action):
        self.svc.window.switch_prev_view('Terminal')

    def on_show_ui(self, action):
        val = action.get_active()
        self.svc.set_opt(action.get_name(), val)
        getattr(self.svc, action.get_name())(val)

class WindowEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
            self.on_document_changed)
        self.subscribe_foreign('editor', 'started',
            self.on_editor_started)

    def on_document_changed(self, document):
        self.svc.update_title(document=document)

    def on_editor_started(self):
        self.svc.boss.hide_splash()
        self.svc.window.show()

class WindowOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_toolbar',
            _('Show the toolbar'),
            bool,
            True,
            _('Whether the main toolbar will be shown'),
            self.on_show_ui,
        )

        self.create_option(
            'show_menubar',
            _('Show the menubar'),
            bool,
            True,
            _('Whether the main menubar will be shown'),
            self.on_show_ui,
        )

        self.create_option(
            'window_title',
            _('Window title'),
            str,
            'Pida - $session - $filename',
            _('Title template for the pida window.\n'
              '$basename : Filename of Document - $filepath : Full filepath \n'
              '$directory : Directory if file - $session : Session name \n'
              '$project_path - $project_name'),
            self.on_title_change,
        )

        self.create_option(
            'project_color',
            _('Project color'),
            Color,
            '#600060',
            _('The color projects shall have in PIDA'),
            self.on_color_change,
        )

        self.create_option(
            'directory_color',
            _('Directory color'),
            Color,
            '#0000c0',
            _('The color directories shall have in PIDA'),
            self.on_color_change,
        )
        

    def on_show_ui(self, client, id, entry, option):
        self.svc.get_action(option.name).set_active(option.get_value())

    def on_color_change(self, client, id, entry, option):
        self.svc.update_colors()
        
    def on_title_change(self, client, id, entry, option):
        self.svc._title_template = None
        self.svc.update_title()

# Service class
class Window(Service):
    """The PIDA Window Manager"""

    commands_config = WindowCommandsConfig
    options_config = WindowOptionsConfig
    actions_config = WindowActionsConfig
    events_config = WindowEvents
    
    def pre_start(self):
        self._title_template = None
        super(Window, self).pre_start()
        self.update_colors()

    def start(self):
        # Explicitly add the permanent views
        for service in ['project', 'filemanager', 'buffer']:
            view = self.boss.cmd(service, 'get_view')
            self.cmd('add_view', paned='Buffer', view=view, removable=False, present=False)
        self._fix_visibilities()
        self.update_colors()
        
    def update_colors(self):
        # set the colors of Document
        Document.markup_directory_color = self.opt('directory_color')
        Document.markup_project_color = self.opt('project_color')

    def update_title(self, document=None):
        if self._title_template is None:
            self._title_template = string.Template(self.opt('window_title'))
        if document is None:
            document = self.boss.cmd('buffer', 'get_current')
        
        subs = {'basename': document.basename or _('New Document'),
                'filepath': document.filename or _('New Document'),
                'directory': document.directory or '',
                'session': session_name(),
                'project_path': document.project and document.project.data_dir or '',
                'project_name': document.project_name
               }
        
        self.window.set_title(self._title_template.safe_substitute(subs))
        

    def _fix_visibilities(self):
        for name in ['show_toolbar', 'show_menubar']:
            val = self.opt(name)
            self.get_action(name).set_active(val)
            getattr(self, name)(val)

    def show_toolbar(self, visibility):
        self.window.set_toolbar_visibility(visibility)

    def show_menubar(self, visibility):
        self.window.set_menubar_visibility(visibility)



# Required Service attribute for service loading
Service = Window



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
