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
import urllib
import gobject

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.actions import ActionsConfig
from pida.core.features import FeaturesConfig
from pida.core.actions import TYPE_REMEMBER_TOGGLE

from pida.ui.views import PidaView, WindowConfig

from pida.utils.gthreads import GeneratorTask, gcall
from pida.utils.web import fetch_url
from pida.utils.feedparser import parse


# locale
from pida.core.locale import Locale
locale = Locale('koders')
_ = locale.gettext

class KodersItem(object):

    def __init__(self, entry):
        print entry
        self.title = entry['title']
        self.link = entry['link']
        self.description = entry['description']


class KodersView(PidaView):

    key = 'koders.list'

    label_text = 'Koders'
    icon_name = 'koders_logo'

    def create_ui(self):
        self._vbox = gtk.VBox(spacing=3)
        self._vbox.set_border_width(6)
        self.add_main_widget(self._vbox)
        self.create_searchbar()
        self.create_list()
        self.create_view()
        self.create_pulsebar()
        self._vbox.show_all()

    def create_searchbar(self):
        h = gtk.HBox()
        self._search_description = gtk.Entry()
        self._search_description.connect('changed', self._on_search_changed)
        l = gtk.Label()
        l.set_text(_('Filter : '))
        h.pack_start(l, expand=False)
        h.pack_start(self._search_description)
        self._vbox.pack_start(h, expand=False)
        self._search_description.show_all()

    def create_list(self):
        self._list = ObjectList(
                [
                    Column('title', data_type=str, title=_('Title'),
                        expand=True),
                ]
        )
        self._list.connect('selection-changed', self._on_list_selected)
        self._list.connect('double-click', self._on_list_double_click)
        self._vbox.pack_start(self._list)
        self._list.show_all()

    def create_view(self):
        self._textview = gtk.TextView()
        self._vbox.pack_start(self._textview, expand=False)
        self._textview.show_all()

    def create_pulsebar(self):
        self.__pulse_bar = gtk.ProgressBar()
        self.__pulse_bar.show_all()
        self.__pulse_bar.set_size_request(-1, 12)
        self.__pulse_bar.set_pulse_step(0.01)
        self._vbox.pack_start(self.__pulse_bar, expand=False)
        self.__pulse_bar.set_no_show_all(True)
        self.__pulse_bar.hide()
        self.add_main_widget(self._vbox, expand=False)

    def append(self, item):
        self._list.append(item)

    def clear(self):
        self._list.clear()

    def can_be_closed(self):
        self.svc.get_action('show_koders').set_active(False)

    def _on_list_selected(self, ot, item):
        self._textview.get_buffer().set_text(item.description)

    def _on_list_double_click(self, ot, item):
        self.svc.browse(url=item.link)

    def _on_search_changed(self, w):
        self.svc.search(pattern=self._search_description.get_text())

    def start_pulse(self):
        self._pulsing = True
        gobject.timeout_add(100, self._pulse)

    def stop_pulse(self):
        self._pulsing = False

    def _pulse(self):
        self.__pulse_bar.pulse()
        return self._pulsing



class KodersActions(ActionsConfig):

    def create_actions(self):
        KodersWindowConfig.action = self.create_action(
            'show_koders',
            TYPE_REMEMBER_TOGGLE,
            _('Koders Viewer'),
            _('Show Koders search window'),
            '',
            self.on_show_koders,
            '',
        )

    def on_show_koders(self, action):
        if action.get_active():
            self.svc.show_koders()
        else:
            self.svc.hide_koders()

class KodersWindowConfig(WindowConfig):
    key = KodersView.key
    label_text = KodersView.label_text

class KodersFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            KodersWindowConfig)

# Service class
class Koders(Service):
    """Browse Koders database"""

    actions_config = KodersActions
    features_config = KodersFeaturesConfig

    def start(self):
        self._view = KodersView(self)
        self._has_loaded = False
        self.task = None

    def show_koders(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_koders(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def browse(self, id):
        self.boss.cmd('browseweb', 'browse', url=(self.url_rfctmpl + id))

    def stop(self):
        if self.task != None:
            self.task.stop()
        if self.get_action('show_koders').get_active():
            self.hide_koders()

    def search(self, pattern, language='', licence=''):
        url = 'http://www.koders.com/?output=rss&s=%s' % pattern
        if language != '':
            url = url + '&la=%s' % language
        if licence != '':
            url = url + '&li=%s' % licence
        self._view.start_pulse()
        fetch_url(url, self.search_callback)

    def search_callback(self, url, data):
        self._view.clear()
        def parse_search(data):
            def parse_result(data):
                feed = parse(data)
                for entry in feed.entries:
                    yield entry
            for entry in parse_result(data):
                yield KodersItem(entry)
        for item in parse_search(data):
            self._view.append(item)
        self._view.stop_pulse()

    def browse(self, url):
        self.boss.cmd('browseweb', 'browse', url=url)

# Required Service attribute for service loading
Service = Koders



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
