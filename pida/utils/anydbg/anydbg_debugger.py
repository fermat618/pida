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

# --- AnyDbg debugger class

class AnyDbg_Debugger:
    def __init__(self, executable, parameters, service, param):
        self._executable = executable
        self._parameters = parameters
        self.svc = service
        self._dbg_param = param

    def start(self):
        """
        First time start: launch the debugger
        Second time start: continue debugging
        """
        raise NotImplementedError

    def stop(self):
        """
        First time stop: reinit the debugger
        Second time stop: end the debugger
        """
        raise NotImplementedError

    def step_in(self):
        """
        Sends the step in function debugger command
        """
        raise NotImplementedError

    def step_over(self):
        """
        Sends the step over function debugger command
        """
        raise NotImplementedError

    def finish(self):
        """
        Sends the finish function debugger command
        """
        raise NotImplementedError

    def toggle_breakpoint(self, file, line):
        """
        Toggle a breakpoint in the debugger
        """
        raise NotImplementedError

