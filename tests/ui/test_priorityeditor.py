

from pida.utils.testing import refresh_gui

from pida.ui.prioritywindow import PriorityEditorView, Category, Entry

class TestCategory(Category):
    @property
    def display(self):
        return self.name

    def __init__(self, name, sub):
        self.name = name
        self.subs = sub
        self._entries = []
        if name != 'cat0':
            self._entries.extend(self._make_entries())
        self._subcats = [TestCategory("%ssub%s" % (name, i), 0)
                        for i in range(sub)]

    def _make_entries(self, default=False):
        for i in xrange(4):
            yield Entry(uid='test%s.%s' % (self.name, i),
                        display="test%s:%s" % (self.name, i),
                        plugin="test",
                        desc="desc")

    def get_entries(self, default=None):
        return self._entries

    def get_subcategories(self):
        return self._subcats

class TestRootCategory(Category):
    def __init__(self, *k):
        self._cats = [TestCategory("cat%s" % i, i % 3)  for i in xrange(4)]

    def get_subcategories(self):
        return self._cats

def pytest_funcarg__view(request):
    view = PriorityEditorView(None, None)
    refresh_gui()
    return view

def test_category_entries():
    t = TestCategory('foo', 2)
    assert t.has_entries
    assert t.has_subcategories

    #XXX evil hack for messing with coverage
    Category.get_entries(t)
    Category.get_subcategories(t)

def test_has_toplevel(view):
    assert view.get_toplevel() is not None

def test_has_no_parent(view):
    assert view.get_toplevel().get_parent() is None

def test_construct_in_simple_mode():
    PriorityEditorView(None, simple=True)

def test_functionality(view):
    root = TestRootCategory()
    view.set_category_root(root)
    view.selection_tree.selected_item = root._cats[1]._subcats[0]
    refresh_gui()
    view.customize_button.toggled()
    view.customize_button.toggled()
    view.selection_tree.selected_item = root._cats[1]._subcats[0]
    refresh_gui()
    view.update_priority_list()
    view.all_languages.toggled()


def test_move_entries(view):
    pl = view.priority_list
    a, b = Entry(a=1), Entry(a=2)

    pl.clear()
    pl.extend((a, b))
    assert list(pl) == [a, b]

    pl.selected_item = a
    view.button_move_down.clicked()
    assert list(pl) == [b, a]

    view.button_move_up.clicked()
    assert list(pl) == [a, b]

def test_update_priority_list(view):
    #XXX: data
    view.update_priority_list()
    view.button_reset.clicked()

def test_close_button(view):
    view.button_close.clicked()


def test_apply_button(view):
    view.button_apply.clicked()


