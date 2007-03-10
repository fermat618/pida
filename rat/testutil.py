__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import unittest
import gtk
import gobject
from util import *

list_children = lambda *args, **kwargs: list(iterate_widget_children(*args, **kwargs))
list_parents = lambda *args, **kwargs: list(iterate_widget_parents(*args, **kwargs))
count_children = lambda *args, **kwargs: len(list_children(*args, **kwargs))
count_parents = lambda *args, **kwargs: len(list_parents(*args, **kwargs))

class TestWidgetIterators(unittest.TestCase):
    def test_count_children(self):
        container = gtk.VBox()

        # The number of children of the container starts at empty
        self.assertEqual(count_children(container), 0)
        # The number of children of the container starts at empty
        self.assertEqual(count_children(container, recurse_children=True), 0)

        container2 = gtk.VBox()
        # Add a sub-container to a container
        container.add(container2)
        # It affects the container where it was added
        
        self.assertEqual(count_children(container), 1)
        assert list_children(container)[0] is container2
        
        # It affects the container where it was added
        self.assertEqual(count_children(container, recurse_children=True), 1)
        assert list_children(container, recurse_children=True)[0] is container2
        
        # The number of children of the sub-container starts at empty
        self.assertEqual(count_children(container2), 0)
        # The number of children of the sub-container starts at empty
        self.assertEqual(count_children(container2, recurse_children=True), 0)

        # Adding a container in the sub-container
        lbl1 = gtk.Label()
        container2.add(lbl1)
        # It does not affect the children of main container
        self.assertEqual(count_children(container), 1)
        self.assertEqual(list_children(container), [container2])
        
        # It affects the list of all children (recurring)
        self.assertEqual(count_children(container, recurse_children=True), 2)
        self.assertEqual(list_children(container, recurse_children=True), [container2, lbl1])

        # It affects the container where it was added
        self.assertEqual(count_children(container2), 1)
        self.assertEqual(list_children(container2), [lbl1])
        
        # It affects the container where it was added
        self.assertEqual(count_children(container2, recurse_children=True), 1)
        self.assertEqual(list_children(container2, recurse_children=True), [lbl1])

        # Adding a child to the main container should not affect the count of elements
        lbl2 = gtk.Label()
        container.add(lbl2)
        self.assertEqual(count_children(container), 2)
        self.assertEqual(list_children(container), [container2, lbl2])
        
        self.assertEqual(count_children(container, recurse_children=True), 3)
        self.assertEqual(list_children(container, recurse_children=True), [container2, lbl1, lbl2])

        self.assertEqual(count_children(container2), 1)
        self.assertEqual(list_children(container2), [lbl1])

        self.assertEqual(count_children(container2, recurse_children=True), 1)
        self.assertEqual(list_children(container2, recurse_children=True), [lbl1])

    def test_iterate_parents(self):
        vbox1 = gtk.VBox()
        self.assertEqual(list_parents(vbox1),[])
        
        vbox2 = gtk.VBox()
        vbox1.add(vbox2)
        self.assertEqual(list_parents(vbox2),[vbox1])

        vbox3 = gtk.VBox()
        vbox1.add(vbox3)
        self.assertEqual(list_parents(vbox3),[vbox1])

        vbox4 = gtk.VBox()
        vbox2.add(vbox4)
        self.assertEqual(list_parents(vbox4),[vbox2, vbox1])

        vbox5 = gtk.VBox()
        vbox4.add(vbox5)
        self.assertEqual(list_parents(vbox5),[vbox4, vbox2, vbox1])
   
    def test_get_root_parent(self):
        # Adding widgets in different depths maintains the root widget
        vbox1 = gtk.VBox()
        self.assertEqual(get_root_parent(vbox1), None)

        vbox2 = gtk.VBox()
        vbox1.add(vbox2)
        self.assertEqual(get_root_parent(vbox2), vbox1)

        vbox3 = gtk.VBox()
        vbox2.add(vbox3)
        self.assertEqual(get_root_parent(vbox3), vbox1)
        self.assertEqual(get_root_parent(vbox2), vbox1)

    def test_find_child_widget(self):
        w1 = gtk.VBox()
        w1.set_name("w1")
        self.assertEqual(find_child_widget(w1, "w1"), w1)
        self.assertEqual(find_child_widget(w1, "foo"), None)
        
        w2 = gtk.VBox()
        w2.set_name("w2")
        w1.add(w2)
        self.assertEqual(find_child_widget(w1, "w2"), w2)
        
        w3 = gtk.VBox()
        w3.set_name("w3")
        w2.add(w3)
        self.assertEqual(find_child_widget(w1, "w3"), w3)
        self.assertEqual(find_child_widget(w2, "w3"), w3)
        self.assertEqual(find_child_widget(w3, "w3"), w3)

    def test_find_parent_widget(self):
        w1 = gtk.VBox()
        w1.set_name("w1")
        self.assertEqual(find_parent_widget(w1, "w1"), w1)
        self.assertEqual(find_parent_widget(w1, "w1", find_self=False), None)
        self.assertEqual(find_parent_widget(w1, "foo"), None)
        
        w2 = gtk.VBox()
        w2.set_name("w2")
        w1.add(w2)
        self.assertEqual(find_parent_widget(w2, "w1"), w1)
        
        w3 = gtk.VBox()
        w3.set_name("w3")
        w2.add(w3)
        self.assertEqual(find_parent_widget(w1, "w1"), w1)
        self.assertEqual(find_parent_widget(w1, "w1", find_self=False), None)
        self.assertEqual(find_parent_widget(w2, "w1"), w1)
        self.assertEqual(find_parent_widget(w3, "w1"), w1)
    
    def test_ListSpec(self):
        spec = ListSpec(("A", gobject.TYPE_STRING), ("B", gobject.TYPE_INT))
        self.assertEqual(spec.A, 0)
        self.assertEqual(spec.B, 1)
        
        store = spec.create_list_store()
        self.assertEqual(store.get_n_columns(), 2)
        self.assertEqual(store.get_column_type(spec.A), gobject.TYPE_STRING)
        self.assertEqual(store.get_column_type(spec.B), gobject.TYPE_INT)
        
        row = spec.to_tree_row({spec.A: "foo", spec.B: 1})
        self.assertEqual(row, ["foo", 1])
        store.append(row)
        
        row = store[0]
        self.assertEqual(row[spec.A], "foo")
        self.assertEqual(row[spec.B], 1)


def main():
    unittest.main()

if __name__ == '__main__':
    main()