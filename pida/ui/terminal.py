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
The PIDA Terminal Widget

The widget `PidaTerminal` encapsulates some of the common functions of VTE in a
more usable format.

"""
from math import floor

import sre

import gtk

from kiwi.utils import gsignal, type_register

from vte import Terminal


class TerminalMatch(object):
    """
    A match for terminal text
    """

    def __init__(self, name, match_re, match_groups_re, callback):
        self.name = name
        self.match_re = match_re
        self.match_groups_re = sre.compile(match_groups_re)
        self.callback = callback

    def __call__(self, *args, **kw):
        self.callback(*args, **kw)


class TerminalMenuMatch(TerminalMatch):
    """
    A match for terminal text that pops up a menu
    """
    def __init__(self, name, match_re, match_groups_re, actions=None):
        TerminalMatch.__init__(self, name, match_re, match_groups_re,
                               self._popup)
        self.actions = []

    def _popup(self, event, *args):
        menu = self._generate_menu(args)
        menu.popup(None, None, None, event.button, event.time)

    def _generate_menu(self, args):
        menu = gtk.Menu()
        for action in self.actions:
            menu_item = action.create_menu_item()
            menu.add(menu_item)
            action.match_args = args
        return menu

    def register_action(self, action):
        """
        Register an action with the menu for this match

        :param action: A gtk.Action
        """
        self.actions.append(action)


class PidaTerminal(Terminal):

    __gtype_name__ = 'PidaTerminal'

    gsignal('match-right-clicked', gtk.gdk.Event, int, str)

    def __init__(self, **kw):
        Terminal.__init__(self)
        self._fix_size()
        self._fix_events()
        self._connect_internal()
        self._init_matches()
        self.set_properties(**kw)

    def set_properties(self, **kw):
        """
        Set properties on the widget
        """
        for key, val in kw.items():
            getattr(self, 'set_%s' % key)(val)

    def _fix_size(self):
        """
        Fix the size of the terminal. Initially the widget starts very large,
        and is unable to be resized by conventional means.
        """
        self.set_size_request(50, 50)

    def _fix_events(self):
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

    def _connect_internal(self):
        """
        Connect the internal signals
        """
        self.connect('button-press-event', self._on_button_press)
        self.connect('match-right-clicked', self._on_match_right_clicked)

    def _init_matches(self):
        """
        Initialize the matching system
        """
        self._matches = {}

    def _get_position_from_pointer(self, x, y):
        """
        Get the row/column position for a pointer position
        """
        cw = self.get_char_width()
        ch = self.get_char_height()
        return int(floor(x / cw)), int(floor(y / ch))

    def _on_button_press(self, term, event):
        """
        Called on a button press
        """
        if event.button == 3:
            col, row = self._get_position_from_pointer(event.x, event.y)
            match = self.match_check(col, row)
            if match is not None:
                match_str, match_num = match
                self.emit('match-right-clicked', event, match_num, match_str)

    def _on_match_right_clicked(self, term, event, match_num, match_str):
        """
        Called when there is a right click on the terminal. Internally, this
        checks whether there has been a match, and fires the required call
        back or menu.
        """
        if match_num in self._matches:
            rematch = self._matches[match_num].match_groups_re.match(match_str)
            match_val = [match_str]
            if rematch is not None:
                groups = rematch.groups()
                if groups:
                    match_val = groups
            self._matches[match_num](event, *match_val)

    def get_named_match(self, name):
        """
        Get a match object for the name
        
        :param name: the name of the match object
        :raises KeyError: If the named match does not exist
        """
        for match in self._matches.values():
            if match.name == name:
                return match
        raise KeyError('No match named "%s" was found' % name)

    def match_add_match(self, match):
        """
        Add a match object.
        """
        match_num = self.match_add(match.match_re)
        self._matches[match_num] = match
        return match_num

    def match_add_callback(self, name, match_str, match_groups, callback):
        """
        Add a match with a callback.

        :param name:            the name of the match
        :param match_str:       the regular expression to match
        :param match_groups:    a regular expression of groups which wil be
                                passed as parameters to the callback function
        :param callback:        the callback function to be called with the result of
                                the match
        """
        match = TerminalMatch(name, match_str, match_groups, callback)
        return self.match_add_match(match)

    def match_add_menu(self, name, match_str, match_groups, menu=None):
        """
        Add a menu match object.
        """
        match = TerminalMenuMatch(name, match_str, match_groups, menu)
        return self.match_add_match(match)

    def match_menu_register_action(self, name, action):
        """
        Register an action with the named match

        :param name: The name of the match
        :param action: A gtk.Action to use in the menu
        """
        self.get_named_match(name).register_action(action)

    def feed_text(self, text, color=None):
        """
        Feed text to the terminal, optionally coloured.
        """
        if color is not None:
            text = '\x1b[%sm%s\x1b[0m' % (color, text)
        self.feed(text)

    def get_all_text(self):
        col, row = self.get_cursor_position()
        return self.get_text_range(0, 0, row, col, lambda *a: True)





class popen(object):
    def __init__(self, cmdargs, callback, kwargs):
        self.__running = False
        self.__readbuf = []
        self.__callback = callback
        self.run(cmdargs, **kwargs)
    
    def run(self, cmdargs, **kwargs):
        console = subprocess.Popen(args=cmdargs, stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT,
                                                 **kwargs)
        self.__running = True
        self.__readtag = gobject.io_add_watch(
            console.stdout, gobject.IO_IN, self.cb_read)
        self.__huptag = gobject.io_add_watch(
            console.stdout, gobject.IO_HUP, self.cb_hup)
        self.pid = console.pid

    def cb_read(self, fd, cond):
        data = os.read(fd.fileno(), 1024)
        self.__readbuf.append(data)
        return True

    def cb_hup(self, fd, cond):
        while True:
            data = os.read(fd.fileno(), 1024)
            if data == '':
                break
            self.__readbuf.append(data)
        self.__callback(''.join(self.__readbuf))
        self.__running = False
        gobject.source_remove(self.__readtag)
        return False




if __name__ == '__main__':
    w = gtk.Window()
    w.resize(400,400)
    t = PidaTerminal(
        word_chars = "-A-Za-z0-9,./?%&#_\\~"
    )
    t.fork_command('bash')
    def mc(event, val):
        print event, val
    t.match_add_callback('python-line', 'line [0-9]+', 'line ([0-9]+)', mc)
    t.match_add_menu('file', r'/[/A-Za-z0-9_\-]+', '')
    a = gtk.Action('open', 'Open', 'Open this file', gtk.STOCK_OPEN)
    b = gtk.Action('save', 'Save', 'Save This File', gtk.STOCK_SAVE)
    def act(action):
        print action.match_args
    t.set_background_image_file('/usr/share/xfce4/backdrops/flower.png')
    a.connect('activate', act)
    t.match_menu_register_action('file', a)
    t.match_menu_register_action('file', b)
    w.add(t)
    w.show_all()
    t.fork_command('bash')

    gtk.main()

