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

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.environment import Environment, get_uidef_path
from pida.core.service import Service
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_TOGGLE, TYPE_NORMAL

from pida.ui.views import PidaView

from pida.utils.gthreads import GeneratorTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('rfc')
_ = locale.gettext

class RfcItem(object):

    def __init__(self, number='0000', data=''):
        self.number = number
        list = re.split('\(([^\(]*)\)', data)
        self.description = list[0]


class RfcView(PidaView):

    label_text = 'RFC'

    def create_ui(self):
        self._vbox = gtk.VBox(spacing=3)
        self._vbox.set_border_width(6)
        self.add_main_widget(self._vbox)
        self.create_toolbar()
        self.create_list()
        self.create_progressbar()
        self._vbox.show_all()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_file(get_uidef_path('rfc-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()

    def create_list(self):
        self._list = ObjectList(
                [
                    Column('number', data_type=str, title=_('Number')),
                    Column('description', data_type=str,
                        title=_('Description'))
                ]
        )
        self._list.connect('double-click', self._on_list_double_click)
        self._vbox.pack_start(self._list)
        self._list.show_all()

    def create_progressbar(self):
        self._progressbar = gtk.ProgressBar()
        self._progressbar.set_text(_('Download RFC Index'))
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

    def append_items(self, items):
        self._list.add_list(items, True)

    def can_be_closed(self):
        self.svc.get_action('show_rfc').set_active(False)

    def _on_list_double_click(self, ot, item):
        self.svc.browse(id=item.number)


class RfcActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_rfc',
            TYPE_TOGGLE,
            _('Rfc Viewer'),
            _('Show the rfc'),
            '',
            self.on_show_rfc,
            '',
        )

        self.create_action(
            'rfc_refreshindex',
            TYPE_NORMAL,
            _('Refresh RFC Index'),
            _('Refresh RFC Index'),
            gtk.STOCK_REFRESH,
            self.on_rfc_refreshindex,
            'NOACCEL',
        )

        self.create_action(
            'rfc_downloadindex',
            TYPE_NORMAL,
            _('Download RFC Index'),
            _('Download RFC Index'),
            gtk.STOCK_GO_DOWN,
            self.on_rfc_downloadindex,
            'NOACCEL',
        )


    def on_show_rfc(self, action):
        if action.get_active():
            self.svc.show_rfc()
        else:
            self.svc.hide_rfc()

    def on_rfc_downloadindex(self, action):
        self.svc.download_index()

    def on_rfc_refreshindex(self, action):
        self.svc.refresh_index()

# Service class
class Rfc(Service):
    """Fetch rfc list and show an rfc"""

    actions_config = RfcActions

    url_rfcindex = 'http://www.ietf.org/iesg/1rfc_index.txt'
    url_rfctmpl = 'http://tools.ietf.org/html/rfc'
    buffer_len = 16384

    def start(self):
        self._filename = os.path.join(Environment.pida_home, 'rfc-index.txt')
        self._view = RfcView(self)
        self._has_loaded = False
        self.counter = 0
        self.task = None
        gcall(self.refresh_index)

    def show_rfc(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_rfc(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def download_index(self):
        if self.task != None:
            self.task.stop()
        self.task = GeneratorTask(self._download_index,
                self.refresh_index)
        self.task.start()

    def refresh_index(self):
        fp = open(self._filename)
        data = ''
        list = []
        zap = True
        for line in fp:
            line = line.rstrip('\n')
            data += line.strip(' ') + ' '
            if line == '':
                t = data.split(' ', 1)
                if zap == False:
                    if data != '' and t[1].strip(' ') != 'Not Issued.':
                        #if t[1].find('Status: UNKNOWN') == -1:
                        list.append(RfcItem(number=t[0], data=t[1]))
                    data = ''
                elif t[0] == '0001':
                    zap = False
                elif zap == True:
                    data = ''
        fp.close()
        self._view.append_items(list)


    def _download_index(self):
        self.get_action('rfc_downloadindex').set_sensitive(False)
        self._view.show_progressbar(True)
        sock = urllib.urlopen(self.url_rfcindex)
        fp = open(self._filename, 'w', 0)
        progress_max = 0
        progress_current = 0
        if sock.headers.has_key('content-length'):
            progress_max = int(sock.headers.getheader('content-length'))
        try:
            while True:
                buffer = sock.read(self.buffer_len)
                if buffer == '':
                    break
                fp.write(buffer)
                progress_current += len(buffer)
                gcall(self._view.update_progressbar, progress_current,
                    progress_max)
        finally:
            sock.close()
            fp.close()

        self._view.show_progressbar(False)
        self.get_action('rfc_downloadindex').set_sensitive(True)
        yield

    def browse(self, id):
        self.boss.cmd('webbrowser', 'browse', url=(self.url_rfctmpl + id))



# Required Service attribute for service loading
Service = Rfc



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
