
from unittest import TestCase

from pida.utils.testing import refresh_gui

from pida.ui.window import PidaWindow
from pida.ui.books import BOOK_TERMINAL, BOOK_PLUGIN
from pida.ui.test_views import TestView

class BasicWindowTest(TestCase):

    def setUp(self):
        self._w = PidaWindow(self)
        refresh_gui()

    def test_basic(self):
        self._w.get_toplevel().show_all()
        refresh_gui()

class AddViewTest(TestCase):

    def setUp(self):
        self._w = PidaWindow(self)
        self._v = TestView(self)

    def test_add_view(self):
        self._w.add_view(BOOK_PLUGIN, self._v)
        refresh_gui()
        self.assertEqual(self._w._book_man.has_view(self._v), True)

    def test_remove_view(self):
        self._w.add_view(BOOK_PLUGIN, self._v)
        refresh_gui()
        self.assertEqual(self._w._book_man.has_view(self._v), True)
        self._w.remove_view(self._v)
        refresh_gui()
        self.assertEqual(self._w._book_man.has_view(self._v), False)

    def test_move_view(self):
        self._w.add_view(BOOK_PLUGIN, self._v)
        self.assertEqual(self._w._book_man.has_view(self._v), True)
        self._w.move_view(BOOK_TERMINAL, self._v)
        refresh_gui()
        self.assertEqual(self._w._book_man.has_view(self._v), True)
        
