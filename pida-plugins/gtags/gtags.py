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
import gtk
import re

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.environment import get_uidef_path
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_REMEMBER_TOGGLE, TYPE_NORMAL
from pida.ui.buttons import create_mini_button

from pida.ui.views import PidaView

from pida.utils.gthreads import GeneratorTask, GeneratorSubprocessTask

# locale
from pida.core.locale import Locale
locale = Locale('gtags')
_ = locale.gettext

class GtagsItem(object):

    def __init__(self, file, line, dataline, symbol, search):
        self.file = file
        self.line = line
        self._dataline = dataline
        self._symbol = symbol
        self.search = search

        self.symbol = self._color_match(symbol, search)
        self.dataline = self._color(dataline, symbol)
        self.filename = '%s:<span color="#000099">%s</span>' % (self.file, self.line)

    def _color_match(self, data, match):
        return data.replace(match, '<span color="#c00000"><b>%s</b></span>' % match)

    def _color(self, data, match):
        return data.replace(match, '<span color="#c00000">%s</span>' % match)

class GtagsView(PidaView):

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

        self._count = 0

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
        self._list = ObjectList(
                [
                    Column('symbol', data_type=str, title=_('Symbol'),
                        use_markup=True),
                    Column('filename', data_type=str, title=_('Location'),
                        use_markup=True),
                    Column('dataline', data_type=str, title=_('Data'),
                        use_markup=True)
                ]
        )
        self._list.connect('double-click', self._on_list_double_click)
        self._vbox.pack_start(self._list)
        self._list.show_all()

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
        self._count += 1
        if self._count == 1:
            self._info.set_text(_('%d match') % self._count)
        else:
            self._info.set_text(_('%d matchs') % self._count)

    def clear_items(self):
        self._list.clear()
        self._count = 0
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
        self.svc.boss.cmd('buffer', 'open_file', file_name=w.file)
        self.svc.boss.editor.goto_line(w.line)

class GtagsActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
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


# Service class
class Gtags(Service):
    """Fetch gtags list and show an gtags"""

    actions_config = GtagsActions
    events_config = GtagsEvents

    def start(self):
        self._view = GtagsView(self)
        self._has_loaded = False
        self._project = self.boss.cmd('project', 'get_current_project')
        self._ticket = 0
        self.task = self._task = None

        acts = self.boss.get_service('window').actions

        acts.register_window(self._view.key,
                             self._view.label_text)


    def show_gtags(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_gtags(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def have_database(self):
        if self._project is None:
            return False
        return os.path.exists(os.path.join(self._project.source_directory, 'GTAGS'))

    def build_db(self):
        if self._project is None:
            return False
        if self.have_database():
            commandargs = ['global', '-v', '-u']
        else:
            commandargs = ['gtags', '-v']
        self._view._refresh_button.set_sensitive(False)
        self.boss.cmd('commander', 'execute',
                commandargs=commandargs,
                cwd=self._project.source_directory,
                title=_('Gtags build...'),
                eof_handler=self.build_db_finished)

    def build_db_finished(self, w):
        self._view.activate(self.have_database())
        self._view._refresh_button.set_sensitive(True)
        self.boss.cmd('notify', 'notify', title=_('Gtags'),
            data=_('Database build complete'))

    def on_project_switched(self, project):
        if project != self._project:
            self._project = project
            self._view.activate(self.have_database())

    def tag_search_current_word(self):
        self.boss.editor.cmd('call_with_current_word', callback=self.tag_search_cw)

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
            if self._view._count > 200:
                self._task.stop()

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
