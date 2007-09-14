# -*- coding: utf-8 -*- 
"""
    filesearch.filesearch
    ~~~~~~~~~~~~~~~~~~~~~

    This file contains the UI-related functions of the file search plugin.

    The search itself is inside ``search.py``, the search filters inside
    ``filters.py``.

    :copyright: 2007 by Benjamin Wiegand.
    :license: GNU GPL, see LICENSE for more details.
"""

import gtk

from os import path
from kiwi.ui.objectlist import Column

from pida.core.locale import Locale
from pida.ui.views import PidaGladeView
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask

from filters import ValidationError, FileNameMatchesFilter
from search import get_filters, do_search


locale = Locale('filesearch')
_ = locale.gettext


class SearchView(PidaGladeView):

    gladefile = 'search'
    locale = locale
    label_text = _('File Search')
    filters = []
    added_filters = []
    running = False

    def create_ui(self):
        # filter select
        self.filter_select.prefill(get_filters())

        self.match_list.set_columns([
            Column('icon_stock_id', use_stock=True, title=' '),
            Column('state_markup', use_markup=True, title=' '),
            Column('markup', use_markup=True, title=_('Name')),
            Column('path', title=_('Path'))
        ])

        # add standard filter
        self.new_filter(FileNameMatchesFilter)

        # task for asynchrounus searching
        # ``append_to_match_list`` is called if a match was found
        # ``search_finished`` is called at the end of search
        self.task = GeneratorTask(do_search, self.append_to_match_list,
                                  self.search_finished)


    def on_add_button__clicked(self, btn):
        # get selected filter
        f = self.filter_select.read()
        self.new_filter(f)

    def on_search_button__clicked(self, btn):
        if not self.running:
            if self.validate():
                self.start()
        else:
            self.stop()

    def on_match_list__row_activated(self, rowitem, search_match):
        self.svc.boss.cmd('buffer', 'open_file',
                          file_name=path.join(search_match.path,
                                              search_match.name))
        self.svc.boss.editor.cmd('grab_focus')

    def can_be_closed(self):
        self.stop()
        return True

    def start(self):
        self.running = True
        self.match_list.clear()
        self.update_match_count(0)
        self.search_button.set_label(gtk.STOCK_STOP)
        # start async search task.
        self.task.start(self.get_search_folder(), self.filters)

    def stop(self):
        self.task.stop()
        self.search_finished()

    def new_filter(self, f):
        entries = f.get_entries()
        box = gtk.HBox(False, 5)
        box.pack_start(gtk.Label(f.description), expand=False)

        for name, entry in entries.iteritems():
            box.pack_start(entry)

        self.filter_box.pack_start(box)
        box.show_all()
        self.filters.append(f(**entries))

    def set_search_folder(self, folder):
        self.select_folder.set_current_folder(folder)

    def get_search_folder(self):
        # XXX: or project path
        return self.select_folder.get_current_folder()

    def validate(self):
        for f in self.filters:
            try:
                f.validate()
            except ValidationError, e:
                # XXX
                return False

        return True

    def update_match_count(self, count=None):
        if count is None:
            self.match_count += 1
        else:
            self.match_count = 0
        self.count_label.set_text('%s files' % self.match_count)

    def append_to_match_list(self, match):
        self.match_list.append(match)
        self.update_match_count()
        self.update_match_count()

    def search_finished(self):
        self.running = False
        self.search_button.set_label(gtk.STOCK_FIND)

class SearchEvents(EventsConfig):

    def create_events(self):
        # XXX: add events
        pass

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('filemanager', 'browsed_path_changed',
                                     self.svc.change_search_folder)


class SearchActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_search',
            TYPE_TOGGLE,
            _('File Search'),
            _('Show the File Search'),
            gtk.STOCK_INFO,
            self.on_show_search,
            '<Shift><Control>f',
        )


    def on_show_search(self, action):
        if action.get_active():
            self.svc.show_search()
        else:
            self.svc.hide_search()


class Search(Service):
    """Search service"""

    actions_config = SearchActions
    events_config = SearchEvents

    def pre_start(self):
        self._view = SearchView(self)

    def change_search_folder(self, path):
        self._view.set_search_folder(path)


    def show_search(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_search(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def ensure_view_visible(self):
        action = self.get_action('show_search')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'presnet_view', view=self._view)

    def stop(self):
        if self.get_action('show_search').get_active():
            self.hide_search()


# Required Service attribute for service loading
Service = Search
