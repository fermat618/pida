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

# PIDA Imports
from pida.utils.debugger.debugger import Debugger, \
                                            GenericDebuggerController, \
                                            DebuggerOptionsConfig

class GdbDebuggerOptionsConfig(DebuggerOptionsConfig):
    name = 'gdb'

class GdbDebuggerController(GenericDebuggerController):
    name = 'GDB_DEBUGGER'
    label = 'Debug with gdb'
    svcname = 'debugger_gdb'

# Service class
class Gdb(Debugger):
    """Debug a project with gdb service""" 

    options_config = GdbDebuggerOptionsConfig
    controller_config = GdbDebuggerController

    DEFAULT_DEBUGGER_PATH_OPTION = '/usr/bin/gdb'

    _parser_patterns = { # {{{
#        # line: Current thread is <THREAD>
#        'Current thread is (.*)' :
#            lambda self, m: self.emit('thread', thread=m.group(1)),

        # line: Starting program: <EXEC> <ARGS>
        'Starting program: (.*) (.*)' :
            lambda self, m: self.emit('start_debugging', 
                                                    executable=m.group(1), 
                                                    arguments=m.group(2)),
        # line: *** Blank or comment
        '\*\*\* Blank or comment' : None,
        # line: Breakpoint <N> set in file <FILE>, line <LINE>.
        'Breakpoint (\d+) set in file (.*), line (\d+).' :
            lambda self, m: self.emit('add_breakpoint', 
                                        ident=m.group(1), 
                                        file=m.group(2),
                                        line=m.group(3)),
        # line: Deleted breakpoint <N>
        'Deleted breakpoint (\d+)' :
            lambda self, m: self.emit('del_breakpoint', ident=m.group(1)),
        # line: (<PATH>:<LINE>):  <FUNCTION>
        '\((.*):(\d+)\): (.*)' :
            lambda self, m: self.emit('step', file=m.group(1), 
                                                  line=m.group(2), 
                                                  function=m.group(3)),
        '--Call--' : 
            lambda self, m: self.emit('function_call'),
        '--Return--' : 
            lambda self, m: self.emit('function_return')
   }
# }}}                

# private methods
    def _parse(self, data):
        """
        Parses a string of output and execute the correct command
        @param data line of output
        """
        for pattern in self._parser_patterns:
            m = re.search(pattern, data)
            if m is not None:
                if self._parser_patterns[pattern] is not None:
                    self._parser_patterns[pattern](self,m)

    def _send_cmd(self, cmd):
        """
        Sends a command to the debugger
        """
        if self._is_running:
            os.write(self._console.master, cmd + '\n')
            return True
        return False

# implementation of the interface
    def init(self):
        """
        Initiates the debugging session
        """
        gdb_path = self.get_option('gdb_executable_path').value
        commandargs = [gdb_path, "--cd="+self._controller.get_cwd(),
                                            "--args",
                                            self._executable, 
                                            self._parameters]

        self._console = self.boss.cmd('commander','execute',
                                            commandargs=commandargs,
                                            cwd=self._controller.get_cwd(), 
                                            title='gdb',
                                            icon=None,
                                            use_python_fork=True,
                                            parser_func=self._parse)
        self._console.can_be_closed = self._end

        if self._console is not None:
            return True
        return False

    def end(self):
        """
        Ends the debugging session
        """
        self._send_cmd('quit')
        self._console = None
        return True

    def step_in(self):
        """
        step in instruction
        """
        self._send_cmd('step')
        
    def step_over(self):
        """
        Step over instruction
        """
        self._send_cmd('next')

    def cont(self):
        """
        Continue execution
        """
        self._send_cmd('continue')

    def finish(self):
        """
        Jump to end of current function
        """
        self._send_cmd('return')

    def add_breakpoint(self, file, line):
        self._send_cmd('break '+file+':'+str(line))

    def del_breakpoint(self, file, line):
        self._send_cmd('clear '+file+':'+str(line))

# Required Service attribute for service loading
Service = Gdb

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
