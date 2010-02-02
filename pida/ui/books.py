# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

ORIENTATION_SIDEBAR_LEFT = 0
ORIENTATION_SIDEBAR_RIGHT = 1

BOOK_TERMINAL = 'Terminal'
BOOK_EDITOR = 'Editor'
BOOK_BUFFER = 'Buffer'
BOOK_PLUGIN = 'Plugin'

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

class BaseBookConfig(object):
    
    def __init__(self, orientation):
        self._orientation = orientation

    def get_tabs_visible(self):
        return True

    def get_tab_position(self):
        return gtk.POS_TOP

    def get_notebook_name(self):
        raise NotImplementedError(_('Must at least define a notebook name'))

    def get_name(self):
        raise NotImplementedError(_('Must at least define a Name'))

    def create_tab_label(self, icon, text):
        if None in [icon, text]:
            return None
        label = gtk.Label(text)
        if self.get_tab_position() in [gtk.POS_TOP, gtk.POS_BOTTOM]:
            b_factory = gtk.HBox
        else:
            b_factory = gtk.VBox
            label.set_angle(270)
        b = b_factory(spacing=2)
        b.pack_start(icon)
        b.pack_start(label)
        b.show_all()
        return b




class TerminalBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'br_book'
        else:
            return 'bl_book'

    def get_name(self):
        return 'Terminal'


class EditorBookConfig(BaseBookConfig):
    
    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'tr_book'
        else:
            return 'tl_book'

    def get_tabs_visible(self):
        return False

    def get_name(self):
        return 'Editor'


class BufferBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'tl_book'
        else:
            return 'tr_book'

    def get_tab_position(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return gtk.POS_RIGHT
        else:
            return gtk.POS_LEFT

    def get_name(self):
        return 'Buffer'

class PluginBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'bl_book'
        else:
            return 'br_book'

    def get_tab_position(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return gtk.POS_RIGHT
        else:
            return gtk.POS_LEFT
    
    def get_name(self):
        return 'Plugin'

class BookConfigurator(object):
    
    def __init__(self, orientation):
        self._orientation = orientation
        self._configs = {}
        self._books = {}
        self._widget_names = {}
        for conf in [
            TerminalBookConfig,
            EditorBookConfig,
            PluginBookConfig,
            BufferBookConfig
        ]:
            book_config = conf(self._orientation)
            self._configs[book_config.get_name()] = book_config
            self._widget_names[book_config.get_notebook_name()] = book_config

    def get_config(self, name):
        try:
            return self._configs[name]
        except KeyError:
            print self._configs
            raise KeyError(_('No Notebook attests to having that name %s') % name)

    def configure_book(self, name, book):
        conf = self._widget_names[name]
        self._books[conf.get_name()] = book
        book.set_show_tabs(conf.get_tabs_visible())
        book.set_tab_pos(conf.get_tab_position())
        book.remove_page(0)
        if conf.get_name() != BOOK_EDITOR:
            # Cannot drag to the editor terminal for now
            book.set_group_id(0)

    def get_book(self, name):
        return self._books[name]

    def get_books(self):
        return self._books.items()


    def get_names(self):
        return self._books.keys()


class BookManager(object):

    def __init__(self, configurator):
        self._conf = configurator
        self._views = dict()
        for k in self._conf.get_names():
            self._views[k] = dict()

    def add_view(self, bookname, view):
        if not self.has_view(view):
            self._views[bookname][id(view)] = view
            book = self._get_book(bookname)
            tab_label = self._create_tab_label(
                bookname,
                view.create_tab_label_icon(),
                view.label_text,
                )
            book.append_page(view.get_toplevel(),
                tab_label=tab_label)
            book.set_current_page(-1)
            book.show_all()
            book.set_tab_detachable(view.get_toplevel(), True)
            self._focus_page(bookname)
        else:
            raise ValueError(_('This view is already in the manager'))

    def remove_view(self, view):
        book_name = self._get_book_for_view(view)
        book = self._get_book(book_name)
        book.remove(view.get_toplevel())
        del self._views[book_name][id(view)]

    def move_view(self, bookname, view):
        self.remove_view(view)
        self.add_view(bookname, view)

    def has_view(self, view):
        return id(view) in self._get_view_ids()

    def next_page(self, bookname):
        book = self._get_book(bookname)
        if self._get_current_page(bookname) == book.get_n_pages() - 1:
            book.set_current_page(0)
        else:
            book.next_page()
        self._focus_page(bookname)

    def prev_page(self, bookname):
        book = self._get_book(bookname)
        if self._get_current_page(bookname) == 0:
            book.set_current_page(book.get_n_pages() - 1)
        else:
            book.prev_page()
        self._focus_page(bookname)

    def _get_current_page(self, bookname):
        return self._get_book(bookname).get_current_page()

    def _focus_page(self, bookname):
        book = self._get_book(bookname)
        book.get_nth_page(book.get_current_page()).grab_focus()

    def _get_book(self, name):
        return self._conf.get_book(name)
        
    def _get_book_for_view(self, view):
        for name, views in self._views.items():
            if id(view) in views:
                return name
        raise ValueError(_('View is not in any Notebook'))

    def _get_view_ids(self):
        uids = []
        for book in self._views.values():
            uids.extend(book.keys())
        return uids

    def _create_tab_label(self, bookname, icon, text):
        conf = self._conf.get_config(bookname)
        return conf.create_tab_label(icon, text)
        





