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

from kiwi.ui.objectlist import Column
from pida.ui.views import PidaGladeView, PidaView
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask

# Imports should be properly arranged as in coding-style.txt
import gtk, gobject, os, re, sre_constants, cgi

class GrepperItem(object):
    # Doctrings should be <= 80 chars wide
    # Docstrings should also have a first line as a summary
    """
    A match item in grepper.
    
    Contains the data for the matches path, and linenumber that if falls on, as
    well as actual line of code that matched, and the matches data.
    """
    # These are comment / doscstrings, not part of the docstring
    # TODO: Highlight match in line
    # TODO: Format some of the other data.

    def __init__(self, path, linenumber=None, line=None, matches=None):
        self._path = path
        self._line = line
        self._matches = matches
        self.linenumber = linenumber
        self.path = self._escape_text(self._path)
        self.line = self._format_line()

    # really dislike this use of the property decorator
    # it's just personal, but I prefer get_foo, then foo = property(get_foo)
    # then at least get_foo remains as a method
    # We don't need properties anyway, we should cache the result, since it
    # won't change, and objectlist refreshes its view a lot

    #@property
    #def path(self):
    #    return cgi.escape(self._path)

    #@property
    #def line(self):
    #    return cgi.escape(self._line)

    def _markup_match(self, text):
        return ('<span color="#c00000"><b>%s</b></span>' %
                self._escape_text(text))

    def _escape_text(self, text):
        return cgi.escape(text)

    # This has to be quite ugly since we need to markup and split and escape as
    # we go along. Since once we have escaped things, we won't know where they
    # are
    #
    def _format_line(self):
        line = self._line
        line_pieces = []
        for match in self._matches:
            # split the line into before the match, and after
            # leaving the after for searching
            prematch, line = line.split(match, 1)
            line_pieces.append(self._escape_text(prematch))
            line_pieces.append(self._markup_match(match))
        # Append the remainder
        line_pieces.append(self._escape_text(line))
        return ''.join(line_pieces)
            


class GrepperActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_grepper',
            TYPE_TOGGLE,
            'Find in files',
            'Show the grepper view',
            gtk.STOCK_FIND,
            self.on_show_grepper,
            '<Shift><Control>g'
        )

    def on_show_grepper(self, action):
        if action.get_active():
            self.svc.show_grepper()
        else:
            self.svc.hide_grepper()


class GrepperView(PidaGladeView):
    gladefile = 'grepper-window'
    label_text = 'Grepper'
    icon_name = gtk.STOCK_FIND

    def create_ui(self):
        # Instance methods should be instance methods
        self.grepper_dir = ''
        self.matches_list.set_columns([
            Column('linenumber', editable=False, title="#",),
            # Only expand the line column (path with autofit)
            Column('path', editable=False, use_markup=True),
            Column('line', expand=True, editable=False, use_markup=True),
            ])
        # Can connect this automatically
        #self.matches_list.connect('row-activated', self.on_match_activated)
        self.path_entry.insert_text(os.path.expanduser('~/'))

    def on_matches_list__row_activated(self, rowitem, grepper_item):
        self.svc.boss.cmd('buffer', 'open_file', file_name=grepper_item.path)

    def append_to_matches_list(self, grepper_item):
        self.matches_list.append(grepper_item)

    def on_find_button__clicked(self, button):
        self.start_grep()

    def on_pattern_entry__activate(self, entry):
        self.start_grep()

    def on_path_entry__activate(self, entry):
        self.start_grep()

    def start_grep(self):
        self.matches_list.clear()
        pattern = self.pattern_entry.get_text()
        location = os.path.normpath(self.path_entry.get_text())
        recursive = self.recursive.get_active()

        # data checking is done here as opposed to in the grep functions
        # because of threading
        if not os.path.exists(location):
            self.svc.boss.get_window().error_dlg('path does not exist')
            return False

        try:
            regex = re.compile(pattern)
        except sre_constants.error, e:
            self.svc.boss.get_window().error_dlg('improper regex')
            return False

        task = GeneratorTask(self.svc._grep, self.append_to_matches_list)
        task.start(location, regex, recursive)


class GrepperCommandsConfig(CommandsConfig):
    
    # Are either of these commands necessary?
    def get_view(self):
        return self.svc.get_view()

    def present_view(self):
        return self.svc.boss.cmd('window', 'present_view', view=self.svc.get_view())

class Grepper(Service):
    # format this docstring
    """
    Grepper is a graphical grep tool used for search through the contents of files for a given regular expression. 
    """
    actions_config = GrepperActionsConfig

    BINARY_RE = re.compile(r'[\000-\010\013\014\016-\037\200-\377]|\\x00')

    def start(self):
        self._view = GrepperView(self)

    def show_grepper(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)

    def hide_grepper(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def _grep(self, top, regex, recursive=False, show_hidden=False):
        """
        _grep is a wrapper around _grep_file_list and _grep_file.
        """
        if os.path.isfile(top):
            file_results = self._grep_file(top, regex)
            for result in file_results:
                yield result
        elif recursive:
            for root, dirs, files in os.walk(top):
                for matches in self._grep_file_list(files, root, regex):
                    yield matches
        else:
            for matches in self._grep_file_list(os.listdir(top), top, regex):
                yield matches

    def _grep_file_list(self, file_list, root, regex, show_hidden=False):
        """
        takes as it's arguments a list of files to grep, the directory containing that list, and a regular expression to search for in them (optionaly whether or not to search hidden files).

        _grep_file_list itterates over that file list, and calls _grep_file on each of them with the supplied arguments
        """
        for file in file_list:
            if file[0] == "." and not show_hidden:
                continue
            filename = "%s/%s" % (root, file,)
            file_results = self._grep_file(filename, regex)
            for result in file_results:
                yield result

    def _grep_file(self, filename, regex):
        """
        takes as it's arguments a full path to a file, and a regular expression to search for. It returns a generator that yields a GrepperItem for each cycle, that contains the path, line number and matches data
        """
        try:
            f = open(filename, 'r')
            for linenumber, line in enumerate(f):
                if self.BINARY_RE.search(line):
                    break

                line_matches = regex.findall(line)

                if len(line_matches):
                    # strip() the line to give the view more vertical space
                    yield GrepperItem(filename, linenumber, line.strip(), line_matches)
        except IOError:
            pass

Service = Grepper

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
