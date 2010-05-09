# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os, re, cgi
import gtk, gobject

from glob import fnmatch

from pygtkhelpers.ui.objectlist import Column
from pida.ui.views import PidaView
from pida.core.charfinder import detect_text
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig
from pida.core.actions import ActionsConfig
from pida.utils.gthreads import GeneratorTask

# locale
from pida.core.locale import Locale
locale = Locale('grepper')
_ = locale.gettext

class GrepperItem(object):
    """
    A match item in grepper.
    
    Contains the data for the matches path, and linenumber that if falls on, as
    well as actual line of code that matched, and the matches data.
    """

    def __init__(self, path, manager, linenumber=None, line=None, matches=None):
        self._manager = manager
        self._path = path
        self._line = line
        self._matches = matches
        self.linenumber = linenumber
        self.path = self._escape_text(self._path)
        self.line = self._format_line()

    def _markup_match(self, text):
        if len(self._manager._views):
            color = self._manager._views[0].matches_list.\
                        style.lookup_color('pida-match')
        else:
            color = None
        if color:
            #color = color.to_string() # gtk 2.12 or higher
            color = "#%04x%04x%04x" % (color.red, color.green, color.blue)
        if not color:
            color = "red"
        return ('<span color="%s"><b>%s</b></span>' %
                (color, self._escape_text(text)))

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
            # ignore empty string matches
            if not match:
                continue
            # this should never happen
            if match not in line:
                continue
            # split the line into before the match, and after
            # leaving the after for searching
            prematch, line = line.split(match, 1)
            line_pieces.append(self._escape_text(prematch))
            line_pieces.append(self._markup_match(match))
        # Append the remainder
        line_pieces.append(self._escape_text(line))
        # strip() the line to give the view more vertical space
        return ''.join(line_pieces).strip()


class GrepperActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_grepper',
            gtk.Action,
            _('Find _in files'),
            _('Show the grepper view'),
            gtk.STOCK_FIND,
            self.on_show_grepper,
            '<Shift><Control>g'
        )

        self.create_action(
            'grep_current_word',
            gtk.Action,
            _('Find word in _project'),
            _('Find the current word in the current project'),
            gtk.STOCK_FIND,
            self.on_grep_current_word,
            '<Shift><Control>question'
        )

        self.create_action(
            'grep_current_word_file',
            gtk.Action,
            _('Find word in document _directory'),
            _('Find the current word in current document directory'),
            gtk.STOCK_FIND,
            self.on_grep_current_word_file,
            '<Shift><Control><Alt>question'
        )

        self.create_action(
            'show_grepper_search',
            gtk.Action,
            _('Find in directory'),
            _('Find in directory'),
            gtk.STOCK_FIND,
            self.on_grep_dir_menu
        )

    def on_grep_dir_menu(self, action):
        self.svc.show_grepper(action.contexts_kw['dir_name'])

    def on_show_grepper(self, action):
        self.svc.show_grepper_in_project_source_directory()

    def on_grep_current_word(self, action):
        self.svc.grep_current_word()

    def on_grep_current_word_file(self, action):
        document = self.svc.boss.cmd('buffer', 'get_current')
        if document is not None:
            self.svc.grep_current_word(document.directory)
        else:
            self.svc.error_dlg(_('There is no current document.'))


class GrepperView(PidaView):
    gladefile = 'grepper_window'
    locale = locale
    label_text = _('Find in Files')
    icon_name = gtk.STOCK_FIND

    def create_ui(self):
        self.grepper_dir = ''
        self.matches_list.set_columns([
            Column('linenumber', editable=False, title="#",),
            Column('path', editable=False, use_markup=True, sorted=True),
            Column('line', expand=True, editable=False, use_markup=True),
            ])

        # we should set this to the current project I think
        self.path_chooser.set_filename(os.path.expanduser('~/'))

        self._history = gtk.ListStore(gobject.TYPE_STRING)
        self.pattern_combo.set_model(self._history)
        self.pattern_combo.set_text_column(0)
        self.recursive.set_active(True)
        self.re_check.set_active(True)
        self.pattern_entry = self.pattern_combo.child
        self.pattern_entry.connect('activate', self._on_pattern_entry_activate)

        self.task = GeneratorTask(self.svc.grep, self.append_to_matches_list,
                                  self.grep_complete, pass_generator=True)
        self.running = False

    def on_matches_list__item_activated(self, ol, item):
        self.svc.boss.cmd('buffer', 'open_file', file_name=item.path,
                                                 line=item.linenumber)
        self.svc.boss.editor.cmd('grab_focus')

    def append_to_matches_list(self, grepper_item):
        # select the first item (slight hack)
        select = not len(self.matches_list)
        self.matches_list.append(grepper_item, select=select)

    def on_find_button__clicked(self, button):
        if self.running:
            self.stop()
            self.grep_complete()
        else:
            self.start_grep()

    def on_current_folder__clicked(self, button):
        cpath = self.svc.boss.cmd('filemanager', 'get_browsed_path')
        self.path_chooser.set_current_folder(cpath)

    def _on_pattern_entry_activate(self, entry):
        self.start_grep()

    def _translate_glob(self, glob):
        # ensure we dont just match the end of the string
        return fnmatch.translate(glob).rstrip('$').replace(r'\Z', '')

    def set_location(self, location):
        self.path_chooser.set_filename(location)
        # setting the location takes a *long* time
        self._hacky_extra_location = location

    def start_grep_for_word(self, word):
        if not word:
            self.svc.error_dlg(_('Empty search string'))
            self.close()
        else:
            self.pattern_entry.set_text(word)
            # very unlikely that a selected text is a regex
            self.re_check.set_active(False)
            self.start_grep()

    def start_grep(self):
        self.matches_list.clear()
        pattern = self.pattern_entry.get_text()
        self._history.insert(0, (pattern,))
        self.pattern_combo.set_active(0)
        location = self.path_chooser.get_filename()
        if location is None:
            location = self._hacky_extra_location
        recursive = self.recursive.get_active()

        self.matches_list.grab_focus()

        # data checking is done here as opposed to in the grep functions
        # because of threading
        if not pattern:
            self.svc.error_dlg(_('Empty search string'))
            return False

        if not os.path.exists(location):
            self.svc.boss.error_dlg(_('Path does not exist'))
            return False

        if not self.re_check.get_active():
            pattern = self._translate_glob(pattern)

        try:
            regex = re.compile(pattern)
        except Exception, e:
            # More verbose error dialog
            self.svc.error_dlg(
                _('Improper regular expression "%s"') % pattern,
                str(e))
            return False

        self.grep_started()
        self.task.start(location, regex, recursive)

    def can_be_closed(self):
        self.stop()
        return True

    def close(self):
        self.svc.boss.cmd('window', 'remove_view', view=self)

    def grep_started(self):
        self.running = True
        self.progress_bar.show()
        gobject.timeout_add(100, self.pulse)
        self.find_button.set_label(gtk.STOCK_STOP)

    def grep_complete(self):
        self.running = False
        self.find_button.set_label(gtk.STOCK_FIND)
        self.progress_bar.hide()

    def pulse(self):
        self.progress_bar.pulse()
        return self.running

    def stop(self):
        self.task.stop()
        self.grep_complete()


class GrepperCommandsConfig(CommandsConfig):
    
    # Are either of these commands necessary?
    def get_view(self):
        return self.svc.get_view()

    def present_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_view())

class GrepperOptions(OptionsConfig):

    def create_options(self):
        self.create_option(
            'maximum_results',
            _('Maximum Results'),
            int,
            500,
            _('The maximum number of results to find (approx).'),
        )

class GrepperEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
            self.svc.set_current_project)

class GrepperFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc, 'grepper-dir-menu.xml'))



class Grepper(Service):
    # format this docstring
    """
    Search text in files.

    Grepper is a graphical grep tool used for search through the contents of
    files for a given match or regular expression. 
    """
    actions_config = GrepperActionsConfig
    events_config = GrepperEvents
    options_config = GrepperOptions
    features_config = GrepperFeatures

    def pre_start(self):
        self.current_project_source_directory = None
        self._views = []

    def show_grepper_in_project_source_directory(self):
        if self.current_project_source_directory is None:
            path = os.getcwd()
        else:
            path = self.current_project_source_directory
        return self.show_grepper(path)

    def show_grepper(self, path):
        view = GrepperView(self)
        view.set_location(path)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=view)
        self._views.append(view)
        return view

    def grep_current_word(self, path=None):
        if path is None:
            view = self.show_grepper_in_project_source_directory()
        else:
            view = self.show_grepper(path)
        self.boss.editor.cmd('call_with_selection_or_word',
                             callback=view.start_grep_for_word)

    def grep(self, top, regex, recursive=False, show_hidden=False,
             generator_task=None):
        """
        grep is a wrapper around _grep_file_list and _grep_file.
        """
        self._result_count = 0
        if os.path.isfile(top):
            file_results = self._grep_file(top, regex)
            for result in file_results:
                yield result
        elif recursive:
            for root, dirs, files in os.walk(top):
                if generator_task.is_stopped:
                    return
                # Remove hidden directories
                if os.path.basename(root).startswith('.') and not show_hidden:
                    del dirs[:]
                    continue
                for matches in self._grep_file_list(files, root, regex,
                                                generator_task=generator_task,
                                                show_hidden=show_hidden):
                    yield matches
        else:
            for matches in self._grep_file_list(os.listdir(top), top, regex,
                                                generator_task=generator_task,
                                                show_hidden=show_hidden):
                yield matches

    def _grep_file_list(self, file_list, root, regex, show_hidden=False,
                                               generator_task=None):
        """
        Grep for a list of files.

        takes as it's arguments a list of files to grep, the directory
        containing that list, and a regular expression to search for in them
        (optionaly whether or not to search hidden files).

        _grep_file_list itterates over that file list, and calls _grep_file on
        each of them with the supplied arguments.
        """
        for file in file_list:
            if generator_task and generator_task.is_stopped:
                return
            if self._result_count > self.opt('maximum_results'):
                break
            if file.startswith(".") and not show_hidden:
                continue
            # never do this, always use os.path.join
            # filename = "%s/%s" % (root, file,)
            filename = os.path.join(root, file)
            file_results = self._grep_file(filename, regex)
            for result in file_results:
                yield result

    def _grep_file(self, filename, regex):
        """
        Grep a file.

        Takes as it's arguments a full path to a file, and a regular expression
        to search for. It returns a generator that yields a GrepperItem for
        each cycle, that contains the path, line number and matches data.
        """
        try:
            if not detect_text(None, filename, None):
                return

            f = open(filename, 'r')

            for linenumber, line in enumerate(f):
                # enumerate is 0 based, line numbers are 1 based
                linenumber = linenumber + 1

                line_matches = regex.findall(line)

                if line_matches:
                    self._result_count += 1
                    yield GrepperItem(filename, self, linenumber, line, line_matches)
        except IOError:
            pass

    def set_current_project(self, project):
        self.current_project_source_directory = project.source_directory
        #self.set_view_location(project.source_directory)

    def set_view_location(self, directory):
        self._view.set_location(directory)

    def stop(self):
        for view in self._views:
            view.stop()


Service = Grepper

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
