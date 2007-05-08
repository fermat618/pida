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

from pida.utils.anydbg.anydbg_debugger import AnyDbg_Debugger

class AnyDbg_gdb(AnyDbg_Debugger):
    """
    Class to interface with a gdb-compatible debugger.
    """
    _console = None
    _breakpoints = []
    
    _parser_patterns = {
#        # line: Current thread is <THREAD>
#        'Current thread is (.*)' :
#            lambda self, m: self.svc.emit('thread', thread=m.group(1)),
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
        """
        Debugger's parsing method
        @param data line of output
        """
        for pattern in self._parser_patterns:
            m = re.search(pattern, data)
            if m is not None:
                if self._parser_patterns[pattern] is not None:
                    self._parser_patterns[pattern](self,m)

    def _send_command(self,command):
        """
        Method to send a command
        @param command gdb command to be sent
        """
        os.write(self._console.master, command + '\n')

    def _jump_to_line(self, event, data, foo=None):
        """
        Jump to buffer and line given in data
        """
        m = re.search('^\((.*):(.*)\):.*$', data)
        if m is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=m.group(1))
            self.svc.boss.editor.cmd('goto_line', line=m.group(2))

    def init(self):
        """
        Initiate the debugger
        """
        gdb_path = self._dbg_param['path']
        commandargs = [gdb_path, "--cd="+self.svc._controller.get_cwd(),
                        self._executable,self._parameters]

        self._console = self.svc.boss.cmd('commander','execute',
                                            commandargs=commandargs,
                                            cwd=self.svc._controller.get_cwd(), 
                                            title='gdb',
                                            icon=None,
                                            use_python_fork=True,
                                            parser_func=self._parse)
        self._console.can_be_closed = self.on_close_clicked

        if self._executable is not None:
            self.svc.emit('start_debugging', executable=self._executable, 
                                             arguments=self._parameters)
    
    def on_close_clicked(self):
        self.svc.end_dbg_session()
        return True

    def end(self):
        """
        Ends the debugger
        """
        self.on_close_clicked()

    def start(self):
        if self._console == None:
            self.init()
        else:
            self._send_command('continue')

    __stop_state = False
    def stop(self):
        if self._console == None:
            self.window.error_dlg('Tried to stop a non-working debugger')
        if self.__stop_state is False:
            self._send_command('restart')
            self._send_command('file bin/pida')
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

