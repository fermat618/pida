
from unittest import TestCase

from pida.utils.testing import refresh_gui

from pida.ui.window import PidaWindow
from pida.ui.books import BOOK_TERMINAL, BOOK_PLUGIN
from tests.ui.test_views import TestView

class BasicWindowTest(TestCase):

    def setUp(self):
        self._w = PidaWindow(self)
        refresh_gui()

    def test_basic(self):
        self._w.get_toplevel().show_all()
        refresh_gui()

