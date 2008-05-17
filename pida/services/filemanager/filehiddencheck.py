# -*- coding: utf-8 -*- 

# Copyright (c) 2008 The PIDA Project

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

SCOPE_PROJECT  = 0
SCOPE_GLOBAL = 1

class FileHiddenCheck(object):
    """A File Hidden Check"""
    _identifier = ""
    _label = ""
    _scope = SCOPE_GLOBAL

    def __init__(self, boss):
        self.boss = boss
    
    def __call__(self, name, path, state):
        """checks if a file is hidden"""

    @property
    def identifier(self):
        """returns a unique identifier"""
        return self._identifier

    @property
    def label(self):
        """returns a label displayed in hidden check menu"""
        return self._label
    
    @property
    def scope(self):
        """returns if selection should be saved globally or per project"""
        return self._scope

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
