
from pida.utils.testing import refresh_gui

from pida.ui.window import PidaWindow
from pida.ui.books import BOOK_TERMINAL, BOOK_PLUGIN

class BasicWindowTest(object):

    def setUp(self):
        self._w = PidaWindow(self)
        refresh_gui()

    def setup_method(self, method):
        self.setUp()

    def test_basic(self):
        self._w.get_toplevel().show_all()
        refresh_gui()

