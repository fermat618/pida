
from unittest import TestCase

from pida.utils.testing import refresh_gui

from pida.ui.views import PidaView

import pida.ui.window
from pida.ui.prioritywindow import PriorityEditorView, Category, Entry

class TestCategory(Category):
    @property
    def display(self):
        return self.name

    def __init__(self, name, sub):
        self.name = name
        self.subs = sub

    def get_entries(self, default=False):
        if self.name == 'cat0':
            return
        for i in xrange(4):
            yield Entry(uid='test%s.%s' %(self.name,i),
                        display="test%s:%s" %(self.name,i),
                        plugin="test",
                        desc="desc")

    def get_subcategories(self):
        for i in xrange(self.subs):
            yield TestCategory("%ssub%s" %(self.name, i), 0)

class TestRootCategory(Category):
    def get_subcategories(self):
        for i in xrange(4):
            yield TestCategory("cat%s" %i, i%3)


class TestPriorityEditorView(PriorityEditorView):
    pass

class TestPriorityEditor(TestCase):

    def setUp(self):
        self._v = TestPriorityEditorView(self, None)
        refresh_gui()

    def test_has_toplevel(self):
        self.assertNotEqual(self._v.get_toplevel(), None)

    def test_has_no_parent(self):
        self.assertEqual(self._v.get_toplevel().get_parent(), None)

    def test_simple_mode(self):
        t2 = TestPriorityEditorView(None, simple=True)

    def test_functionality(self):
        root = TestRootCategory()
        self._v.set_category_root(root)
