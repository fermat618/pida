# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005 Ali Afshar aafshar@gmail.com

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

"""
========================
The PIDA Terminal Widget
========================

"""
from math import floor

import sre

import gtk

from kiwi.utils import gsignal, type_register

from vte import Terminal

class PidaTerminal(Terminal):

    __gtype_name__ = 'PidaTerminal'

    gsignal('match-right-clicked', int, str)

    def __init__(self):
        Terminal.__init__(self)
        self._fix_size()
        self._fix_events()
        self._connect_internal()
        self._init_matches()

    def _init_matches(self):
        self._match_callbacks = {}
        self._match_res = {}

    def _fix_size(self):
        self.set_size_request(50, 50)
        
    def _fix_events(self):
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

    def _connect_internal(self):
        self.connect('button-press-event', self._on_button_press)
        self.connect('match-right-clicked', self._on_match_right_clicked)

    def _get_position_from_pointer(self, x, y):
        cw = self.get_char_width()
        ch = self.get_char_height()
        return int(floor(x / cw)), int(floor(y / ch))

    def _on_button_press(self, term, event):
        if event.button == 3:
            col, row = self._get_position_from_pointer(event.x, event.y)
            match = self.match_check(col, row)
            if match is not None:
                match_str, match_num = match
                self.emit('match-right-clicked', match_num, match_str)

    def _on_match_right_clicked(self, term, match_num, match_str):
        if match_num in self._match_callbacks:
            rematch = self._match_res[match_num].match(match_str)
            match_val = [match_str]
            if rematch is not None:
                groups = rematch.groups()
                if groups:
                    match_val = groups
            self._match_callbacks[match_num](*match_val)

    def match_add_with_callback(self, match_str, callback):
        match_num = self.match_add(match_str)
        self._match_callbacks[match_num] = callback
        self._match_res[match_num] = sre.compile(match_str)






if __name__ == '__main__':
    w = gtk.Window()
    t = PidaTerminal()
    t.fork_command('bash')
    def mc(val):
        print val
    t.match_add_with_callback('line ([0-9]+)', mc)
    w.add(t)
    w.show_all()
    gtk.main()

