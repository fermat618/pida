__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2006, Tiago Cogumbreiro"

import unittest
import gtk

from shiftpaned import ShiftPaned, SHOW_BOTH, SHOW_CHILD1, SHOW_CHILD2

class TestPaned(unittest.TestCase):
    def setUp(self):
        self.paned = ShiftPaned()

    def assertChild(self, *widget):
        # Calls the super, dirty hack to get the real elements
        children = tuple(self.paned.get_children())
        self.assertEquals(widget, children)

    def assertState(self, state):
        self.assertEquals(state, self.paned.get_state())
        
    def test_paned(self):
        # It is initially empty
        self.assertChild()
        
        # When it contains only one element it remains empty
        lbl1 = gtk.Label("left")
        self.paned.pack1(lbl1)
        self.assertChild(lbl1)
        self.assertEquals(self.paned.child1_widget, lbl1)
        
        # When it contaisn two elements it cointains the container of the
        # elements of the given type
        lbl2 = gtk.Label("right")
        self.paned.pack2(lbl2)
        self.assertChild(lbl1, lbl2)
        self.assertEquals(self.paned.child2_widget, lbl2)
        
        # It should begin on 'SHOW_BOTH' state
        self.assertState(SHOW_BOTH)
        self.paned.pack2(lbl2)
        
        # Changing it to SHOW_BOTH does no effect
        self.paned.set_state(SHOW_BOTH)
        self.assertChild(lbl1, lbl2)

        # Their children should be now filled
        self.paned.set_state(SHOW_CHILD1)
        self.assertChild(lbl1)
        self.assertChild(self.paned.child1_widget)

        # Changing it to SHOW_BOTH does no effect
        self.paned.set_state(SHOW_BOTH)
        self.assertChild(lbl1, lbl2)
                
        # Now show the right
        self.paned.set_state(SHOW_CHILD2)
        self.assertChild(lbl2)
        self.assertChild(self.paned.child2_widget)

        # Their children should be now filled
        self.paned.set_state(SHOW_CHILD1)
        self.assertChild(self.paned.child1_widget)

        # Changing it to SHOW_BOTH does no effect
        self.paned.set_state(SHOW_BOTH)
        self.assertChild(lbl1, lbl2)

        # Now show the right
        self.paned.set_state(SHOW_CHILD2)
        self.assertChild(lbl2)
        self.assertChild(self.paned.child2_widget)

        # Changing it to SHOW_BOTH does no effect
        self.paned.set_state(SHOW_BOTH)
        self.assertChild(lbl1, lbl2)



if __name__ == '__main__':
    unittest.main()


