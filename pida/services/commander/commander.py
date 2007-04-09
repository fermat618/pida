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

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import BaseView
from pida.ui.terminal import PidaTerminal

class CommanderActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'shell',
            TYPE_NORMAL,
            'Run Shell',
            'Open a shell prompt',
            'terminal',
            self.execute_shell
        )

    def execute_shell(self, action):
        self.svc.cmd('execute_shell')

class CommanderCommandsConfig(CommandsConfig):

    def execute(self, commandargs):
        self.svc.execute(commandargs)

    def execute_shell(self):
        self.execute(['bash'])

class TerminalView(BaseView):

    icon_name = 'terminal'

    def create_ui(self):
        self._term = PidaTerminal()
        self.pida_widget.add_main_widget(self._term)
        self._term.show()

    def execute(self, commandargs):
        self._term.fork_command(commandargs[0], commandargs)

# Service class
class Commander(Service):
    """Describe your Service Here""" 

    commands_config = CommanderCommandsConfig
    actions_config = CommanderActionsConfig

    def start(self):
        self._terminals = []

    def execute(self, commandargs):
        t = TerminalView(self)
        t.execute(commandargs)
        self.boss.add_view('Terminal', t)


# Required Service attribute for service loading
Service = Commander



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79: