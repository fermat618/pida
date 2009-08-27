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
import gzip
import tempfile
import threading
import xml.sax
import xml.dom.minidom as minidom

xml.sax.handler.feature_external_pes = False

import gtk
import gobject
from kiwi.ui.objectlist import ObjectTree, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.ui.views import PidaGladeView, WindowConfig

from pida.utils.gthreads import GeneratorTask, AsyncTask

# locale
from pida.core.locale import Locale
locale = Locale('library')
_ = locale.gettext

class LibraryView(PidaGladeView):

    key = 'library.list'
    
    _columns = [
        Column('title', expand=True, sorted=True)
    ]

    gladefile = 'library_viewer'
    locale = locale
    icon_name = 'gtk-library'
    label_text = _('Documentation')

    def create_ui(self):
        self.books_list.set_columns(self._columns)
        self.contents_tree.set_columns(self._columns)
        self.books_list.set_headers_visible(False)
        self.contents_tree.set_headers_visible(False)

    def fetch_books(self):
        self.books_list.clear()
        self.contents_tree.clear()
        task = GeneratorTask(fetch_books, self.add_book)
        task.start()

    def add_book(self, item):
        self.books_list.append(item)

    def on_books_list__double_click(self, ol, item):
        self.contents_tree.clear()
        if item is not None:
            task = AsyncTask(self.load_book, self.book_loaded)
            task.start()

    def on_contents_tree__double_click(self, ot, item):
        self.svc.browse_file("file://%s" %item.path)

    def load_book(self):
        item = self.books_list.get_selected()
        return item.load()
        
    def book_loaded(self, bookmarks):
        self.contents_tree.clear()
        task = GeneratorTask(bookmarks.get_subs, self.add_bookmark)
        task.start()
        self.view_book.set_current_page(1)

    def add_bookmark(self, bookmark, parent):
        self.contents_tree.append(parent, bookmark)

    def on_refresh_button__clicked(self, button):
        self.fetch_books()

    def can_be_closed(self):
        self.svc.get_action('show_library').set_active(False)


class LibraryActions(ActionsConfig):

    def create_actions(self):
        LibraryWindowConfig.action = self.create_action(
            'show_library',
            TYPE_REMEMBER_TOGGLE,
            _('Documentation Library'),
            _('Show the documentation library'),
            '',
            self.on_show_library,
            '<Shift><Control>r',
        )

        self.create_action(
            'show_browser',
            TYPE_REMEMBER_TOGGLE,
            _('Documentation Browser'),
            _('Documentation Browser'),
            '',
            self.on_show_browser,
        )

    def on_show_library(self, action):
        if action.get_active():
            self.svc.show_library()
        else:
            self.svc.hide_library()

    def on_show_browser(self, action):
        if action.get_active():
            self.svc.show_browser()
        else:
            self.svc.hide_browser()

def fetch_books():
    dirs = ['/usr/share/gtk-doc/html',
            '/usr/share/devhelp/books',
            os.path.expanduser('~/.devhelp/books')]
    
    use_gzip = True#self.opts.book_locations__use_gzipped_book_files
    for dir in dirs:
        for book in fetch_directory(dir):
            yield book

def fetch_directory(directory):
    if os.path.exists(directory):
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.exists(path):
                load_book = Book(path, True)
                yield load_book





class TitleHandler(xml.sax.handler.ContentHandler):

    def __init__(self):
        self.title = _('untitled')
        self.is_finished = False

    def startElement(self, name, attributes):
        self.title = attributes['title']
        self.is_finished = True


class Book(object):

    def __init__(self, path, include_gz=True):
        self.directory = path
        self.key = path
        self.name = os.path.basename(path)
        self.bookmarks = None
        try:
            self.short_load()
        except (OSError, IOError):
            pass

    def has_load(self):
        return self.bookmarks is not None

    def short_load(self):
        config_path = None
        path = self.directory
        if not os.path.isdir(path):
            return
        for name in os.listdir(path):
            if name.endswith('.devhelp'):
                config_path = os.path.join(path, name)
                break
            elif name.endswith('.devhelp.gz'):
                gz_path = os.path.join(path, name)
                f = gzip.open(gz_path, 'rb', 1)
                gz_data = f.read()
                f.close()
                fd, config_path = tempfile.mkstemp()
                os.write(fd, gz_data)
                os.close(fd)
                break
        self.title = None
        if config_path:
            parser = xml.sax.make_parser()
            parser.setFeature(xml.sax.handler.feature_external_ges, 0)
            handler = TitleHandler()
            parser.setContentHandler(handler)
            f = open(config_path)
            for line in f:
                try:
                    parser.feed(line)
                except:
                    raise
                if handler.is_finished:
                    break
            f.close()
            self.title = handler.title
        if not self.title:
            self.title = os.path.basename(path)

    def load(self):
        config_path = None
        path = self.directory
        for name in os.listdir(path):
            if name.endswith('.devhelp'):
                config_path = os.path.join(path, name)
                break
            elif name.endswith('.devhelp.gz'):
                gz_path = os.path.join(path, name)
                f = gzip.open(gz_path, 'rb', 1)
                gz_data = f.read()
                f.close()
                fd, config_path = tempfile.mkstemp()
                os.write(fd, gz_data)
                os.close(fd)
                break
        if config_path and os.path.exists(config_path):
            dom = minidom.parse(config_path)
            main = dom.documentElement
            book_attrs = dict(main.attributes)
            for attr in book_attrs:
                setattr(self, attr, book_attrs[attr].value)
            self.chapters = dom.getElementsByTagName('chapters')[0]
            self.root = os.path.join(self.directory, self.link)
            self.bookmarks = self.get_bookmarks()
        else:
            for index in ['index.html']:
                indexpath = os.path.join(path, index)
                if os.path.exists(indexpath):
                    self.root = indexpath
                    break
                self.root = indexpath

        self.key = path
        return self.get_bookmarks()

    def get_bookmarks(self):
        root = BookMark(self.chapters, self.directory)
        root.name = self.title
        root.path = self.root
        return root


class BookMark(object):

    def __init__(self, node, root_path):
        try:
            self.name = node.attributes['name'].value
        except:
            self.name = None
        self.title = self.name
        try:
            self.path = os.path.join(root_path, node.attributes['link'].value)
        except:
            self.path = None
        self.key = self.path
        self.subs = []
        for child in self._get_child_subs(node):
            bm = BookMark(child, root_path)
            self.subs.append(bm)

    def _get_child_subs(self, node):
        return [n for n in node.childNodes if n.nodeType == 1]

    def get_subs(self, parent=None):
        if parent is None:
            aparent = self
        else:
            aparent = parent
        for sub in aparent.subs:
            yield sub, parent
            for csub in self.get_subs(sub):
                yield csub
                
    def __iter__(self):
            yield None, sub

class LibraryWindowConfig(WindowConfig):
    key = LibraryView.key
    label_text = LibraryView.label_text

class LibraryFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            LibraryWindowConfig)

# Service class
class Library(Service):
    """Describe your Service Here""" 

    actions_config = LibraryActions
    features_config = LibraryFeaturesConfig

    def start(self):
        self._view = LibraryView(self)
        bclass = self.boss.cmd('browseweb', 'get_web_browser')
        self._browser = bclass(self)
        self._browser.label_text = _('Documentation')
        self._browser.connect_closed(self._on_close_clicked)
        self._has_loaded = False

    def show_library(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True
            self._view.fetch_books()

    def hide_library(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def _on_close_clicked(self, button):
        self.get_action('show_browser').set_active(False)

    def show_browser(self):
        self.boss.cmd('window', 'add_view', paned='Terminal',
                      view=self._browser)

    def hide_browser(self):
        self.boss.cmd('window', 'remove_view', view=self._browser)

    def ensure_browser_visible(self):
        if not self.get_action('show_browser').get_active():
            self.get_action('show_browser').set_active(True)
        self.boss.cmd('window', 'present_view', view=self._browser)

    def browse_file(self, url):
        self.ensure_browser_visible()
        self._browser.fetch(url)

    def stop(self):
        if self.get_action('show_library').get_active():
            self.hide_library()
        if self.get_action('show_browser').get_active():
            self.hide_browser()


# Required Service attribute for service loading
Service = Library



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
