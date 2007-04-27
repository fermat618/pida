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

import gtk

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.environment import get_uidef_path

from pida.ui.views import PidaView

from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall

class BookmarkItem(object):

    def _init_(self, group='none', title='no title', data=None):
        self.group = group
        self.title = title
        self.data = data
        self._cache_pixbuf = None

    def run(self, service):
        pass

    def get_markup(self):
        return '%s' % self.title
    markup = property(get_markup)


class BookmarkItemFile(BookmarkItem):

    def _init_(self, title='no title', data=None):
        BookmarkItem._init_(self, group='file', title=title, data=data)

    def run(self, service):
        service.boss.cmd('buffermanager', 'open_file', filename=self.data)

class BookmarkItemPath(BookmarkItem):

    ICON_NAME = 'folder'

    def _init_(self, title='no title', data=None):
        BookmarkItem._init_(self, group='path', title=title, data=data)

    def run(self, service):
        service.boss.cmd('filemanager', 'browse', directory=self.data)

"""
class BookmarkItemUrl(BookmarkItem):

    ICON_NAME = 'www'

    def _init_(self, title='no title', data=None):
        BookmarkItem._init_(self, group='url', title=title, data=data)

    def run(self, service):
        service.boss.call_command('webbrowser', 'browse', url=self.data)
"""


class BookmarkView(PidaView):

    icon_name = 'gnome-library'
    label_text = 'Bookmarks'

    def create_ui(self):
        self._vbox = gtk.VBox()
        self.create_toolbar()
        self.create_ui_list()
        self.add_main_widget(self._vbox)
        self._vbox.show_all()

    def create_ui_list(self):
        self._books = gtk.Notebook()
        self._list_files = ObjectList([Column('markup', data_type=str, use_markup=True)])
        self._list_files.set_headers_visible(False)
        self._books.append_page(self._list_files,
                tab_label=gtk.Label('Files'))
        self._list_dirs = ObjectList([Column('markup', data_type=str, use_markup=True)])
        self._list_dirs.set_headers_visible(False)
        self._books.append_page(self._list_dirs,
                tab_label=gtk.Label('Dirs'))
        """
        self._list_url = ObjectList([Column('markup', data_type=str, use_markup=True)])
        self._list_url.set_headers_visible(False)
        self._books.add(self._list_url)
        """
        self._vbox.add(self._books)
        self._books.show_all()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_file(get_uidef_path('bookmark-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()

class BookmarkActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_bookmark',
            TYPE_TOGGLE,
            'Bookmark Viewer',
            'Show bookmarks',
            '',
            self.on_show_bookmark,
            '<Shift><Control>b',
        )

        self.create_action(
            'bookmark_curfile',
            TYPE_NORMAL,
            'Bookmark current file',
            'Bookmark current file',
            'text-x-generic',
            self.on_bookmark_curfile,
            'NOACCEL',
        )

        self.create_action(
            'bookmark_curdir',
            TYPE_NORMAL,
            'Bookmark current directory',
            'Bookmark current directory',
            'stock_folder',
            self.on_bookmark_curdir,
            'NOACCEL',
        )


    def on_show_bookmark(self, action):
        if action.get_active():
            self.svc.show_bookmark()
        else:
            self.svc.hide_bookmark()

    def on_bookmark_curdir(self, action):
        pass

    def on_bookmark_curfile(self, action):
        pass

# Service class
class Bookmark(Service):
    """Manage bookmarks"""

    actions_config = BookmarkActions

    def start(self):
        self._view = BookmarkView(self)
        self._has_loaded = False

    def show_bookmark(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_bookmark(self):
        self.boss.cmd('window', 'remove_view', view=self._view)


# Required Service attribute for service loading
Service = Bookmark



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
