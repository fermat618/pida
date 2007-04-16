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

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig, OTypeString, OTypeBoolean, OTypeInteger
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal

class CommanderOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'font',
            'Terminal Font',
            OTypeString,
            'Monospace 10',
            'The font used in terminals',
        )

        self.create_option(
            'transparent',
            'Terminal Transparency',
            OTypeBoolean,
            False,
            'Whether terminals will be transparent',
        )

        self.create_option(
            'use_background_image',
            'Use a background image',
            OTypeBoolean,
            False,
            'Whether a background image will be displayed',
        )

        self.create_option(
            'background_image_file',
            'Background image file',
            OTypeString,
            '',
            'The file used for the background image',
        )

        self.create_option(
            'cursor_blinks',
            'Cursor Blinks',
            OTypeBoolean,
            False,
            'Whether the cursor will blink'
        )

        self.create_option(
            'scrollback_lines',
            'Scrollback line numer',
            OTypeInteger,
            100,
            'The number of lines in the terminal scrollback buffer',
        )

class CommanderActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'shell',
            TYPE_NORMAL,
            'Run Shell',
            'Open a shell prompt',
            'terminal',
            self.execute_shell,
            '<Shift><Control>T',
        )

    def execute_shell(self, action):
        self.svc.cmd('execute_shell')

class CommanderCommandsConfig(CommandsConfig):

    def execute(self, commandargs, env=[], cwd=os.getcwd(), title='Command',
                      icon='terminal'):
        self.svc.execute(commandargs, env, cwd, title, icon)

    def execute_shell(self, env=[], cwd=os.getcwd(), title='Shell'):
        self.svc.execute(['bash'], env=env, cwd=cwd, title=title, icon=None)


class TerminalView(PidaView):

    icon_name = 'terminal'

    def create_ui(self):
        self._term = PidaTerminal(**self.svc.get_options())
        self.add_main_widget(self._term)
        self._term.show()

    def execute(self, commandargs, env, cwd):
        self._term.fork_command(commandargs[0], commandargs, env, cwd)


# Service class
class Commander(Service):
    """Describe your Service Here""" 

    commands_config = CommanderCommandsConfig
    actions_config = CommanderActionsConfig
    options_config = CommanderOptionsConfig

    def start(self):
        self._terminals = []

    def execute(self, commandargs, env, cwd, title, icon):
        t = TerminalView(self, title, icon)
        t.execute(commandargs, env + ['PIDA_TERM=1'], cwd)
        self.boss.add_view('Terminal', t, True)
        self._terminals.append(t)


    def get_options(self):
        options = dict(
            font_from_string=self.opt('font'),
            background_transparent=self.opt('transparent'),
            cursor_blinks=self.opt('cursor_blinks'),
            scrollback_lines=self.opt('scrollback_lines'),
        )
        if self.opt('use_background_image'):
            imagefile = self.opt('background_image_file')
            options['background_image_file'] = imagefile
        return options



# Required Service attribute for service loading
Service = Commander



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
