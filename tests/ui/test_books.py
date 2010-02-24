
from unittest import TestCase

import gtk

from pida.ui.books import BookConfigurator, BookManager
from pida.ui.books import ORIENTATION_SIDEBAR_LEFT, ORIENTATION_SIDEBAR_RIGHT
from pida.ui.books import BOOK_TERMINAL, BOOK_EDITOR

from pida.utils.testing import refresh_gui
from pida.utils.testing.mock import Mock

class TestConfig(TestCase):

    def setUp(self):
        self._SL = BookConfigurator(ORIENTATION_SIDEBAR_LEFT)
        self._SR = BookConfigurator(ORIENTATION_SIDEBAR_RIGHT)

        self._nbSL = dict(
            tl_book=gtk.Notebook(),
            tr_book=gtk.Notebook(),
            bl_book=gtk.Notebook(),
            br_book=gtk.Notebook(),
        )

        self._nbSR = dict(
            tl_book=gtk.Notebook(),
            tr_book=gtk.Notebook(),
            bl_book=gtk.Notebook(),
            br_book=gtk.Notebook(),
        )

        for name, book in self._nbSL.iteritems():
            self._SL.configure_book(name, book)

        for name, book in self._nbSR.iteritems():
            self._SR.configure_book(name, book)

        refresh_gui()

    def test_TerminalBook(self):
        self.assertEqual(self._nbSL['br_book'],
            self._SL.get_book('Terminal'))
        self.assertEqual(self._nbSR['bl_book'],
            self._SR.get_book('Terminal'))

    def test_TerminalBook_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Terminal').get_tab_pos(),
            gtk.POS_TOP
        )
        self.assertEqual(
            self._SR.get_book('Terminal').get_tab_pos(),
            gtk.POS_TOP
        )

    def test_TerminalBook_tab_vis(self):
        self.assertEqual(
            self._SL.get_book('Terminal').get_show_tabs(),
            True
        )
        self.assertEqual(
            self._SR.get_book('Terminal').get_show_tabs(),
            True
        )

    def test_Editor(self):
        self.assertEqual(self._nbSL['tr_book'],
            self._SL.get_book('Editor'))
        self.assertEqual(self._nbSR['tl_book'],
            self._SR.get_book('Editor'))

    def test_Editor_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Editor').get_tab_pos(),
            gtk.POS_TOP
        )
        self.assertEqual(
            self._SR.get_book('Editor').get_tab_pos(),
            gtk.POS_TOP
        )

    def test_Editor_tab_vis(self):
        self.assertEqual(
            self._SL.get_book('Editor').get_show_tabs(),
            False
        )
        self.assertEqual(
            self._SR.get_book('Editor').get_show_tabs(),
            False
        )

    def test_Plugin(self):
        self.assertEqual(self._nbSL['bl_book'],
            self._SL.get_book('Plugin'))
        self.assertEqual(self._nbSR['br_book'],
            self._SR.get_book('Plugin'))

    def test_Plugin_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Plugin').get_tab_pos(),
            gtk.POS_RIGHT
        )
        self.assertEqual(
            self._SR.get_book('Plugin').get_tab_pos(),
            gtk.POS_LEFT
        )

    def test_Plugin_tab_vis(self):
        self.assertEqual(
            self._SL.get_book('Plugin').get_show_tabs(),
            True
        )
        self.assertEqual(
            self._SR.get_book('Plugin').get_show_tabs(),
            True
        )

    def test_Buffer(self):
        self.assertEqual(self._nbSL['tl_book'],
            self._SL.get_book('Buffer'))
        self.assertEqual(self._nbSR['tr_book'],
            self._SR.get_book('Buffer'))

    def test_Buffer_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Buffer').get_tab_pos(),
            gtk.POS_RIGHT
        )
        self.assertEqual(
            self._SR.get_book('Buffer').get_tab_pos(),
            gtk.POS_LEFT
        )

    def test_Buffer_tab_vis(self):
        self.assertEqual(
            self._SL.get_book('Buffer').get_show_tabs(),
            True
        )
        self.assertEqual(
            self._SR.get_book('Buffer').get_show_tabs(),
            True
        )

    def test_bad_name(self):
        def b():
            self._SL.get_book('banana')
        self.assertRaises(KeyError, b)


class TestBookManager(TestCase):

    def setUp(self):
        self._SL = BookConfigurator(ORIENTATION_SIDEBAR_LEFT)

        self._nbSL = dict(
            tl_book=gtk.Notebook(),
            tr_book=gtk.Notebook(),
            bl_book=gtk.Notebook(),
            br_book=gtk.Notebook(),
        )

        w = gtk.Window()
        vb = gtk.VBox()
        w.add(vb)

        for nb in self._nbSL.values():
            vb.pack_start(nb)

        for name, book in self._nbSL.iteritems():
            self._SL.configure_book(name, book)

        self._man = BookManager(self._SL)

        w.show_all()

        refresh_gui()
        def mock_label(l):
            mock = Mock()
            mock.get_toplevel.return_value = gtk.Label(l)
            mock.create_tab_label_icon.return_value = gtk.image_new_from_stock(
                    gtk.STOCK_INFO, gtk.ICON_SIZE_MENU)
            mock.label_text = 'l'
            return mock
        self._mview1 = mock_label('1')
        self._mview2 = mock_label('2')

    def test_add_view(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self.assertEqual(self._SL.get_book(BOOK_TERMINAL).get_n_pages(), 1)

    def test_has_view(self):
        self.assertEqual(self._man.has_view(self._mview1), False)
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self.assertEqual(self._man.has_view(self._mview1), True)

    def test_add_view_twice(self):
        def add():
            self._man.add_view(BOOK_TERMINAL, self._mview1)
            refresh_gui()
        add()
        self.assertRaises(ValueError, add)

    def test_remove_view(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self.assertEqual(self._SL.get_book(BOOK_TERMINAL).get_n_pages(), 1)
        self._man.remove_view(self._mview1)
        refresh_gui()
        self.assertEqual(self._SL.get_book(BOOK_TERMINAL).get_n_pages(), 0)
        self.assertEqual(self._man.has_view(self._mview1), False)

    def test_remove_nonexistent_view(self):
        def r():
            self._man.remove_view(self._mview1)
        self.assertRaises(ValueError, r)

    def test_move_view(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self.assertEqual(self._SL.get_book(BOOK_TERMINAL).get_n_pages(), 1)
        self._man.move_view(BOOK_EDITOR, self._mview1)
        refresh_gui()
        self.assertEqual(self._SL.get_book(BOOK_TERMINAL).get_n_pages(), 0)
        self.assertEqual(self._SL.get_book(BOOK_EDITOR).get_n_pages(), 1)

    def test_add_2_pages(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self._man.add_view(BOOK_TERMINAL, self._mview2)
        refresh_gui()
        book = self._man._get_book(BOOK_TERMINAL)
        self.assertEqual(book.get_n_pages(), 2)

    def test_prev_page(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self._man.add_view(BOOK_TERMINAL, self._mview2)
        refresh_gui()
        self._man.prev_page(BOOK_TERMINAL)
        refresh_gui()
        self._man.prev_page(BOOK_TERMINAL)
        refresh_gui()
        book = self._man._get_book(BOOK_TERMINAL)
        self.assertEqual(book.get_n_pages(), 2)

    def test_next_page(self):
        self._man.add_view(BOOK_TERMINAL, self._mview1)
        refresh_gui()
        self._man.add_view(BOOK_TERMINAL, self._mview2)
        refresh_gui()
        self._man.next_page(BOOK_TERMINAL)
        refresh_gui()
        self._man.next_page(BOOK_TERMINAL)
        refresh_gui()
        book = self._man._get_book(BOOK_TERMINAL)
        self.assertEqual(book.get_n_pages(), 2)

