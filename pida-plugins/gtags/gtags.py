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

"""
GTags plugins. It utalizes gtags/the gnu global software to provide 
language support
"""


import os
import gtk
import re
from threading import Thread

from pygtkhelpers.ui.objectlist import ObjectList, Column
# PIDA Imports
from pida.core.languages import LanguageService, Completer, \
                                LanguageServiceFeaturesConfig
from pida.utils.languages import Suggestion, LANG_PRIO
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_REMEMBER_TOGGLE, TYPE_NORMAL, ActionsConfig
from pida.core.projects import REFRESH_PRIORITY
from pida.ui.buttons import create_mini_button
import subprocess

from pida.ui.views import PidaView, WindowConfig

from pida.utils.gthreads import GeneratorSubprocessTask

# locale
from pida.core.locale import Locale
locale = Locale('gtags')
_ = locale.gettext

class GtagsItem(object):
    """
    Object which is used to fill the GtagsView list
    """

    def __init__(self, file, line, dataline, symbol, search):
        self.file = file
        self.line = line
        self._dataline = dataline
        self._symbol = symbol
        self.search = search

        self.symbol = self._color_match(symbol, search)
        self.dataline = self._color(dataline, symbol)
        self.filename = '%s:<span color="#000099">%s</span>' % (self.file, 
                                                                self.line)

    def _color_match(self, data, match):
        return data.replace(match, 
                            '<span color="#c00000"><b>%s</b></span>' % match)

    def _color(self, data, match):
        return data.replace(match, 
                            '<span color="#c00000">%s</span>' % match)

class GtagsView(PidaView):
    """
    Window wich shows the seach entry and update button for gtags
    """

    key = 'gtags.list'

    label_text = _('Gtags')

    def create_ui(self):
        self._hbox = gtk.HBox(spacing=3)
        self._hbox.set_border_width(2)
        self.add_main_widget(self._hbox)
        self._vbox = gtk.VBox(spacing=3)
        self._hbox.pack_start(self._vbox)
        self.create_searchbar()
        self.create_list()
        self.create_progressbar()
        self.create_toolbar()
        self._hbox.show_all()

    def create_searchbar(self):
        h = gtk.HBox(spacing=3)
        h.set_border_width(2)
        # label
        l = gtk.Label()
        l.set_text(_('Pattern : '))
        h.pack_start(l, expand=False)
        # pattern
        self._search = gtk.Entry()
        self._search.connect('changed', self._on_search_changed)
        self._search.set_sensitive(False)
        h.pack_start(self._search)
        # info
        self._info = gtk.Label()
        self._info.set_text('-')
        h.pack_start(self._info, expand=False)
        self._vbox.pack_start(h, expand=False)
        self._search.show_all()

    def create_toolbar(self):
        self._bar = gtk.VBox(spacing=1)
        self._refresh_button = create_mini_button(
                gtk.STOCK_REFRESH, _('Build TAGS database'),
                self._on_refresh_button_clicked)
        self._bar.pack_start(self._refresh_button, expand=False)
        self._hbox.pack_start(self._bar, expand=False)
        self._bar.show_all()

    def create_list(self):
        self._list = ObjectList([
            Column('symbol', title=_('Symbol'), use_markup=True),
            Column('filename', title=_('Location'), use_markup=True),
            Column('dataline', title=_('Data'), use_markup=True),
            ])
        self._scroll = gtk.ScrolledWindow()
        self._scroll.add(self._list)
        self._list.connect('item-double-clicked', self._on_list_double_click)
        self._vbox.pack_start(self._scroll)
        self._scroll.show_all()

    def create_progressbar(self):
        self._progressbar = gtk.ProgressBar()
        self._vbox.pack_start(self._progressbar, expand=False)
        self._progressbar.set_no_show_all(True)
        self._progressbar.hide()

    def update_progressbar(self, current, max):
        if max > 1:
            self._progressbar.set_fraction(float(current) / float(max))

    def show_progressbar(self, show):
        self._progressbar.set_no_show_all(False)
        if show:
            self._progressbar.show()
        else:
            self._progressbar.hide()

    def add_item(self, item):
        self._list.append(item)
        #XXX: ngettext
        self._info.set_text('%d matches' % len(self._list))

    def clear_items(self):
        self._list.clear()
        self._info.set_text('-')

    def activate(self, activate):
        self._search.set_sensitive(activate)
        self._list.set_sensitive(activate)

    def can_be_closed(self):
        self.svc.get_action('show_gtags').set_active(False)

    def _on_search_changed(self, w):
        self.svc.tag_search(self._search.get_text())

    def _on_refresh_button_clicked(self, w):
        self.svc.build_db()

    def _on_list_double_click(self, o, w):
        file_name = os.path.join(self.svc._project.source_directory, w.file)
        self.svc.boss.cmd('buffer', 'open_file', file_name=file_name, 
                          line=int(w.line))

class GtagsSuggestion(Suggestion):
    pass


class GtagsCompleter(Completer):

    priority = LANG_PRIO.DEFAULT
    name = "global"
    plugin = "gtags"
    description = _("a per project global completer list")

    def get_completions(self, base, buffer_, offset):
        """
        Gets a list of completitions.
        
        @base - string which starts completions
        @buffer - document to parse
        @offset - cursor position
        """
        if self.document.project and \
           self.svc.have_database(self.document.project):
            # gtags is no good completer and often returns way to much results
            # limiting here is a good thing
            if (not isinstance(base, basestring) and 
                self.svc.opt("min_filter_length")) or (
                self.svc.opt("min_filter_length") > len(base)):

                return

            args = ['global', '-c', base and unicode(base) or '']
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE,
                                    stdin=None, stderr=None, shell=False,
                                    universal_newlines=True,
                                    cwd=self.document.project.source_directory)

            while True:
                line = pipe.stdout.readline()
                if not line:
                    pipe.communicate()
                    return

                yield GtagsSuggestion(line.strip())

        return


class GtagsActions(ActionsConfig):

    def create_actions(self):
        GtagsWindowConfig.action = self.create_action(
            'show_gtags',
            TYPE_REMEMBER_TOGGLE,
            _('Gtags Viewer'),
            _('Show the gtags'),
            '',
            self.on_show_gtags,
            '<Shift><Control>y',
        )

        self.create_action(
            'gtags_current_word_file',
            TYPE_NORMAL,
            _('Complete current word'),
            _('Complete current word'),
            gtk.STOCK_FIND,
            self.on_gtags_current_word,
            '<Control>slash'
        )

    def on_show_gtags(self, action):
        if action.get_active():
            self.svc.show_gtags()
        else:
            self.svc.hide_gtags()

    def on_gtags_current_word(self, action):
        self.svc.tag_search_current_word()

class GtagsEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
                               self.svc.on_project_switched)
        self.subscribe_foreign('buffer', 'document-saved',
                               self.svc.on_document_saved)


class GtagsUpdateThread(Thread):
    def __init__(self, svc, project):
        self.svc = svc
        self.project = project
        self.run_again = True
        self.callbacks = []
        self.clean = False
        super(GtagsUpdateThread, self).__init__()
        self.daemon = True

    def run(self):
        while self.run_again:
            self.run_again = False

            args, cwd = self.svc.build_args(quiet=True, clean=self.clean,
                                            project=self.project)
            if args:
                self.svc.log.debug(
                            _('Run Gtags with %s in %s') %(args, cwd))
                try:
                    pid  = subprocess.Popen(args, stdin=None, 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, 
                                            shell=True, 
                                            cwd=cwd, universal_newlines=True)
                    stdout, stderr = pid.communicate()
                    if pid.returncode:
                        self.svc.log.error(
                             _('Error executing background gtags: %s') %stderr)

                    else:
                        self.svc.log.info(
                             _('Ran gtags in backgroud successfully'))
                except OSError, err:
                    self.svc.log.error(
                         _('Error running gtags %s' %err))

                self.clean = False

                while self.callbacks:
                    callback = self.callbacks.pop()
                    callback()
                    # only run one callback if there is a run_again, the next
                    # callback is for the next run
                    # elsewise clean up by call all of them
                    if self.run_again:
                        break

        # cleanup references
        del self.svc._bg_threads[self.project] 

class GtagsWindowConfig(WindowConfig):
    key = GtagsView.key
    label_text = GtagsView.label_text

class GtagsFeaturesConfig(LanguageServiceFeaturesConfig):
    def subscribe_all_foreign(self):
        super(GtagsFeaturesConfig, self).subscribe_all_foreign()

        self.subscribe_foreign('window', 'window-config',
            GtagsWindowConfig)
        self.subscribe_foreign('project', 'project_refresh',
            self.do_refresh)

    def do_refresh(self, project, callback):
        self.svc.project_refresh(project, callback)
    
    do_refresh.priority = REFRESH_PRIORITY.PRE_FILECACHE

class GtagsOptionsConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
            'min_filter_length',
            _('Min filter length'),
            int,
            3,
            _('Minimum characters for completer to start.'))

# Service class
class Gtags(LanguageService):
    """Fetch gtags list and show an gtags"""

    language_name = ('C', 'Cpp', 'Java', 'Php', 'Yacc', 'Assembly')

    actions_config = GtagsActions
    events_config = GtagsEvents
    features_config = GtagsFeaturesConfig
    options_config = GtagsOptionsConfig
    completer_factory = GtagsCompleter

    def start(self):
        self._view = GtagsView(self)
        self._has_loaded = False
        self._project = None
        self.on_project_switched(self.boss.cmd('project', 
                                               'get_current_project'))
        self._ticket = 0
        self._bg_threads = {}
        self._bd_do_updates = False
        self.task = self._task = None

    def show_gtags(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_gtags(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def have_database(self, project=None):
        if project is None:
            project = self._project

        if project is None:
            return False

        return os.path.exists(os.path.join(self._project.source_directory, 
                                           'GTAGS'))

    def build_args(self, clean=False, quiet=False, project=None):
        """
        Generates the command and cwd the should be run to update database
        """
        if project is None:
            project = self._project

        if not project:
            return None, None

        commandargs = ['gtags', '-v']
        if self.have_database(project) and not clean:
            commandargs.append('-i')
        
        if quiet:
            commandargs.append('-q')

        aconf = project.get_meta_dir('gtags', filename="gtags.conf")
        if os.path.exists(aconf):
            commandargs.extend(['--gtagsconf', aconf])
        afiles = project.get_meta_dir('gtags', filename="files")
        if os.path.exists(afiles):
            commandargs.extend(['-f', afiles])

        return commandargs, project.source_directory

    def build_db(self, clean=False):
        """
        Build/Update the gtags database.
        """
        if self._project is None:
            return False

        commandargs, cwd = self.build_args(clean=clean)

        self._view._refresh_button.set_sensitive(False)
        self.boss.cmd('commander', 'execute',
                commandargs=commandargs,
                cwd=cwd,
                title=_('Gtags build...'),
                eof_handler=self.build_db_finished)

    def build_db_finished(self, term, *args):
        self._view.activate(self.have_database())
        self._view._refresh_button.set_sensitive(True)
        self.boss.cmd('notify', 'notify', title=_('Gtags'),
            data=_('Database build complete'))
        term.on_exited(*args)

    def on_project_switched(self, project):
        if project != self._project and project:
            self._project = project
            self._view.activate(self.have_database())
            self._bgupdate = os.path.exists(self._project.get_meta_dir(
                                                'gtags', 
                                                filename="autoupdate"))
        elif not project:
            self._project = None
            self._bgupdate = False

    def on_document_saved(self, document):
        if not document.doctype or \
           document.doctype.internal not in self.language_name:
            # we only run updates if a document with doctypes we 
            # handle are saved
            return
        pro = self._project
        if not pro:
            return
        
        if pro in self._bg_threads and \
           self._bg_threads[pro].is_alive():
            # mark that daemon should run again
            self._bg_threads[pro].run_again = True
        else:
            self._bg_threads[pro] = GtagsUpdateThread(self, pro)
            self._bg_threads[pro].start()

    def project_refresh(self, project, callback):
        """Runs the gtags update on project refresh"""
        if not self.have_database(project=project):
            callback()
            return

        if project in self._bg_threads and self._bg_threads[project].is_alive():
            # mark that daemon should run again
            self._bg_threads[project].run_again = True
            self._bg_threads[project].callbacks.append(callback)
            self._bg_threads[project].clean = True
        else:
            self._bg_threads[project] = GtagsUpdateThread(self, project)
            self._bg_threads[project].callbacks.append(callback)
            self._bg_threads[project].clean = True
            self._bg_threads[project].start()

    def tag_search_current_word(self):
        self.boss.editor.cmd('call_with_current_word', 
                             callback=self.tag_search_cw)

    def tag_search_cw(self, word):
        self.get_action('show_gtags').set_active(True)
        self._view._list.grab_focus()
        self._view._search.set_text(word)

    def tag_search(self, pattern):
        if not self.have_database() or pattern is None:
            return

        self._view.clear_items()
        if pattern == '':
            return

        if self._task:
            self._task.stop()

        def _line(line):
            match = re.search('([^\ ]*)[\ ]+([0-9]+) ([^\ ]+) (.*)', line)
            if match is None:
                return
            data = match.groups()
            self._view.add_item(GtagsItem(file=data[2],
                line=data[1], dataline=data[3],
                symbol=data[0], search=pattern))
            if len(self._view._list) > 200:
                self._task.stop()

        #FIXME this is not portable
        cmd = 'for foo in `global -c %s`; do global -x -e $foo; done' % pattern
        self._task = GeneratorSubprocessTask(_line)
        self._task.start(cmd, cwd=self._project.source_directory, shell=True)

    def stop(self):
        if self._task:
            self._task.stop()
        if self.get_action('show_gtags').get_active():
            self.hide_gtags()


# Required Service attribute for service loading
Service = Gtags



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
