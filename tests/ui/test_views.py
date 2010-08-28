
from unittest import TestCase

from pida.utils.testing import refresh_gui

from pida.ui.views import PidaView


class TestView(PidaView):

    gladefile = 'test_view'

    def on_b1__clicked(self, button):
        self.svc._clicked = True

class ActionView(PidaView):

    gladefile = 'test_view'

    def on_test_act__activate(self, action):
        self.svc._clicked = True

    def on_b2__clicked(self, button):
        self.svc._clicked = True

class BasicViewTest(TestCase):

    def setUp(self):
        self._v = TestView(self)
        refresh_gui()

    def test_has_toplevel(self):
        self.assertNotEqual(self._v.get_toplevel(), None)

    def test_has_no_parent(self):
        self.assertEqual(self._v.get_toplevel().get_parent(), None)


class ViewCallbackTest(TestCase):

    def setUp(self):
        self._v = TestView(self)
        self._clicked = False
        refresh_gui()

    def test_event_callback(self):
        self.assertEqual(self._clicked, False)
        self._v.b1.clicked()
        refresh_gui()
        self.assertEqual(self._clicked, True)


class ViewActionsTest(TestCase):

    def setUp(self):
        self._v = TestView(self)
        self._clicked = False
        refresh_gui()

    def test_actions(self):
        self.assertEqual(self._clicked, False)
        self._v.test_act.activate()

