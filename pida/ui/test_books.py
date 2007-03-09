
from unittest import TestCase

import gtk

from pida.ui.books import BookConfigurator
from pida.ui.books import ORIENTATION_SIDEBAR_LEFT
from pida.ui.books import ORIENTATION_SIDEBAR_RIGHT
from pida.utils.testing import refresh_gui


class TestConfig(TestCase):

    def setUp(self):
        self._SL = BookConfigurator(ORIENTATION_SIDEBAR_LEFT)
        self._SR = BookConfigurator(ORIENTATION_SIDEBAR_RIGHT)

        self._nbSL = dict(
            tl_book = gtk.Notebook(),
            tr_book = gtk.Notebook(),
            bl_book = gtk.Notebook(),
            br_book = gtk.Notebook(),
        )

        self._nbSR = dict(
            tl_book = gtk.Notebook(),
            tr_book = gtk.Notebook(),
            bl_book = gtk.Notebook(),
            br_book = gtk.Notebook(),
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

    def test_Editor_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Plugin').get_tab_pos(),
            gtk.POS_RIGHT
        )
        self.assertEqual(
            self._SR.get_book('Plugin').get_tab_pos(),
            gtk.POS_LEFT
        )

    def test_Editor_tab_vis(self):
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

    def test_Editor_tab_pos(self):
        self.assertEqual(
            self._SL.get_book('Buffer').get_tab_pos(),
            gtk.POS_RIGHT
        )
        self.assertEqual(
            self._SR.get_book('Buffer').get_tab_pos(),
            gtk.POS_LEFT
        )

    def test_Editor_tab_vis(self):
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
            tl_book = gtk.Notebook(),
            tr_book = gtk.Notebook(),
            bl_book = gtk.Notebook(),
            br_book = gtk.Notebook(),
        )

        for name, book in self._nbSL.iteritems():
            self._SL.configure_book(name, book)

        refresh_gui()

    def test_add_page(self):
        pass
