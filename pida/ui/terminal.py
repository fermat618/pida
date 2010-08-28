# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    The PIDA Terminal Widget
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The widget `PidaTerminal` encapsulates VTE in a more usable api.

    :license:   GPL2 or later
    :copyright:
        2005 Ali Afshar aafshar@gmail.com
"""

import re
import os
import sys
import gobject
import subprocess
import gtk
from collections import defaultdict

from pygtkhelpers.utils import gsignal
#FIXME win32 should get a terminal
if sys.platform != 'win32':
    from vte import Terminal
else:
    #XXX: broken like hell
    class Terminal(object):
        pass

from pida.utils.addtypes import Enumeration

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

EVENTS = Enumeration('CLICK', 'MENU')

class BaseTerminalMatch(object):
    """
    Base class for all Match classes
    """
    def __init__(self, name, match_re, match_groups_re, callback, usr=None):
        self.name = name
        self.match_re = match_re
        self.match_groups_re = re.compile(match_groups_re)
        self.callback = callback
        self.usr = usr

    def __call__(self, *args, **kw):
        self.callback(*args, **kw)

class TerminalMatch(BaseTerminalMatch):
    """
    A match for terminal text
    """
    pass

class TerminalMenuMatch(BaseTerminalMatch):
    """
    This Match has a list of actions that will be added to the menu that will
    be shown.
    
    """
    def __init__(self, name, match_re, match_groups_re, actions=None):
        TerminalMatch.__init__(self, name, match_re, match_groups_re,
                               self._popup)
        self.actions = actions or []

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



class TerminalMenuCallbackMatch(BaseTerminalMatch):
    """
    This match return a list of action items which will be added to the
    menu that will be shown.
    The callback is generating the menu
    """
    def __call__(self, event, *args, **kw):
        menu = self.callback(*args, **kw)
        # Don't popup anything for non matches
        if menu is not None:
            return menu
            #menu.popup(None, None, None, event.button, event.time)


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
        self._matches = defaultdict(list)
        self._matches_res = {}

    def _get_position_from_pointer(self, x, y):
        """
        Get the row/column position for a pointer position
        """
        cw = self.get_char_width()
        ch = self.get_char_height()
        return int(x / cw), int(y / ch)

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
        elif event.button in [1,2] and event.state & gtk.gdk.CONTROL_MASK:
            col, row = self._get_position_from_pointer(event.x, event.y)
            match = self.match_check(col, row)
            if match is not None:
                match_str, match_num = match
                for call in self._matches[match_num]:
                    if not isinstance(call, TerminalMatch):
                        continue
                    match_str, match_num = match
                    match_val = [match_str]
                    rematch = call.match_groups_re.match(match_str)
                    if rematch is not None:
                        groups = rematch.groups()
                        if groups:
                            match_val = groups
                    if call.callback(term, event, match_str, usr=call.usr,
                                    *match_val):
                        break

    def _on_match_right_clicked(self, term, event, match_num, match_str):
        """
        Called when there is a right click on the terminal. Internally, this
        checks whether there has been a match, and fires the required call
        back or menu.
        """
        if match_num in self._matches:
            match_val = [match_str]
            menu = gtk.Menu()

            for call in self._matches[match_num]:
                rematch = call.match_groups_re.match(match_str)
                if rematch is not None:
                    groups = rematch.groups()
                    if groups:
                        match_val = groups
                print match_val

                if not isinstance(call, (TerminalMenuMatch, 
                                         TerminalMenuCallbackMatch)):
                    continue

                first = True
                for action in call.callback(term, event, match_str,
                                            usr=call.usr, *match_val):
                    action.match_args = match_val
                    if isinstance(action, gtk.Action):
                        menu_item = action.create_menu_item()
                    else:
                        menu_item = action
                    if len(menu) and first:
                        menu.add(gtk.SeparatorMenuItem())
                    menu.add(menu_item)
                    first = False

            if len(menu):
                menu.show_all()
                menu.popup(None, None, None, event.button, event.time)


    def get_named_match(self, name):
        """
        Get a match object for the name
        
        :param name: the name of the match object
        :raises KeyError: If the named match does not exist
        """
        for match in self._matches.values():
            if match.name == name:
                return match
        raise KeyError(_('No match named "%s" was found') % name)

    def match_add_match(self, match):
        """
        Add a match object.
        """
        # adding more then one match that does the same is not going to work
        # very well :(
        # instead we register it once and dispatch it later
        if not match.match_re in self._matches_res:
            match_num = self.match_add(match.match_re)
            self._matches_res[match.match_re] = match_num
        else:
            match_num = self._matches_res[match.match_re]

        self._matches[match_num].append(match)

        return match_num

    def match_add_callback(self, name, match_str, match_groups, callback, usr=None):
        """
        Add a match with a callback.

        :param name:            the name of the match
        :param match_str:       the regular expression to match
        :param match_groups:    a regular expression of groups which wil be
                                passed as parameters to the callback function
        :param callback:        the callback function to be called with the result of
                                the match
        """
        match = TerminalMatch(name, match_str, match_groups, callback, usr=usr)
        return self.match_add_match(match)

    def match_add_menu(self, name, match_str, match_groups, menu=None, usr=None):
        """
        Add a menu match object.
        """
        match = TerminalMenuMatch(name, match_str, match_groups, menu, usr=usr)
        return self.match_add_match(match)

    def match_add_menu_callback(self, name, match_str, match_groups, 
                                callback, usr=None):
        """
        Add a match that will result in a menu item for right click
        """
        match = TerminalMenuCallbackMatch(name, match_str, match_groups,
            callback, usr=usr)
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
    a = gtk.Action('open', _('Open'), _('Open this file'), gtk.STOCK_OPEN)
    b = gtk.Action('save', _('Save'), _('Save This File'), gtk.STOCK_SAVE)
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

