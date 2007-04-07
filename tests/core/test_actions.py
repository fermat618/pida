
import gtk

from pida.core.actions import ActionsConfig, TYPE_NORMAL
from unittest import TestCase

from pida.utils.testing import refresh_gui

class MyActions(ActionsConfig):

    def create_actions(self):
        self.create_action('banana', TYPE_NORMAL, 'do a banana', 'bananatt', gtk.STOCK_OPEN)
        self.create_action('banana2', TYPE_NORMAL, 'do a banana', 'bananatt', gtk.STOCK_OPEN,
            self.my_handler)

    def act_banana(self, action):
        self.svc.banana = True

    def my_handler(self, action):
        self.svc.banana = True
        


class ActionTestCase(TestCase):

    def setUp(self):
        self.banana = False
        self.boss = None
        self._acts = MyActions(self)
        self._acts.create()
        self._act = self._acts._actions.get_action('banana')

    def get_name(self):
        return 'testcase'

    def test_action(self):
        self.assertEqual(self.banana, False)
        self._acts._actions.get_action('banana').activate()
        refresh_gui()
        self.assertEqual(self.banana, True)

    def test_label(self):
        self.assertEqual(self._acts.get_action('banana').get_property('label'), 'do a banana')

    def test_tt(self):
        self.assertEqual(self._acts.get_action('banana').get_property('tooltip'), 'bananatt')

    def test_sid(self):
        self.assertEqual(self._acts.get_action('banana').get_property('stock_id'), gtk.STOCK_OPEN)

    def test_action_callback(self):
        self.assertEqual(self.banana, False)
        self._acts._actions.get_action('banana2').activate()
        refresh_gui()
        self.assertEqual(self.banana, True)
