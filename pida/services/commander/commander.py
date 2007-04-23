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
from pida.core.options import OptionsConfig, OTypeString, OTypeBoolean, \
    OTypeInteger, OTypeFile
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal

def get_default_system_shell():
    if 'SHELL' in os.environ:
        return os.environ['SHELL']
    else:
        return 'bash'

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
            OTypeFile,
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

        self.create_option(
            'shell_command',
            'The shell command for shells',
            OTypeString,
            get_default_system_shell(),
            'The command that will be used for shells'
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

        self.create_action(
            'terminal-for-file',
            TYPE_NORMAL,
            'Shell in file directory',
            'Open a shell prompt in the parent directory of this file',
            'terminal',
            self.on_terminal_for_file,
            'NOACCEL',
        )

        self.create_action(
            'terminal-for-dir',
            TYPE_NORMAL,
            'Shell in directory',
            'Open a shell prompt in the directory',
            'terminal',
            self.on_terminal_for_dir,
            'NOACCEL',
        )

    def execute_shell(self, action):
        self.svc.cmd('execute_shell')

    def on_terminal_for_file(self, action):
        cwd = os.path.dirname(action.contexts_kw['file_name'])
        self.svc.cmd('execute_shell', cwd=cwd)

    def on_terminal_for_dir(self, action):
        cwd = action.contexts_kw['dir_name']
        self.svc.cmd('execute_shell', cwd=cwd)
        


class CommanderCommandsConfig(CommandsConfig):

    def execute(self, commandargs, env=[], cwd=os.getcwd(), title='Command',
                      icon='terminal'):
        self.svc.execute(commandargs, env, cwd, title, icon)

    def execute_shell(self, env=[], cwd=os.getcwd(), title='Shell'):
        self.svc.execute([self.svc.opt('shell_command')], env=env, cwd=cwd, title=title, icon=None)

class CommanderFeaturesConfig(FeaturesConfig):

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'commander-file-menu.xml'))
        self.subscribe_foreign_feature('contexts', 'dir-menu',
            (self.svc.get_action_group(), 'commander-dir-menu.xml'))

class TerminalView(PidaView):

    icon_name = 'terminal'

    def create_ui(self):
        self._term = PidaTerminal(**self.svc.get_terminal_options())
        self._term.connect('child-exited', self.on_exited)
        self.add_main_widget(self._term)
        self._term.show()

    def execute(self, commandargs, env, cwd):
        self._term.fork_command(commandargs[0], commandargs, env, cwd)

    def on_exited(self, term):
        self._term.feed_text('Child exited\r\n', '1;34')
        self._term.feed_text('Press any key to close.')
        self._term.connect('commit', self.on_press_any_key)

    def on_press_any_key(self, term, data, datalen):
        self.svc.boss.cmd('window', 'remove_view', view=self)


# Service class
class Commander(Service):
    """Describe your Service Here""" 

    commands_config = CommanderCommandsConfig
    actions_config = CommanderActionsConfig
    options_config = CommanderOptionsConfig
    features_config = CommanderFeaturesConfig

    def start(self):
        self._terminals = []

    def execute(self, commandargs, env, cwd, title, icon):
        t = TerminalView(self, title, icon)
        t.execute(commandargs, env + ['PIDA_TERM=1'], cwd)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=t)
        self._terminals.append(t)

    def get_terminal_options(self):
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
