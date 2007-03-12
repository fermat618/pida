__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2006, Tiago Cogumbreiro"

import gtk

HIDE_BOTH = 0
SHOW_CHILD1 = 1
SHOW_CHILD2 = 2
SHOW_BOTH = 3


def _state_to_operation(old_state, new_state):
    result = new_state - old_state
    if result == 1:
        return "_add_child"
    if result == -1:
        return "_remove_child"

def _get_operations(old_state, new_state):
    """
    how get operation works is really simple, there are two booleans packed in
    an integer, namely 'state'.
    The first bit is child 1, the second bit is referring to child 2.
    So, using the binary notation, the state is like this:
     * 00 then it means that child 1 is hidden and so is child 2.
     * 01 means that child 1 is visible and child 2 is not.
     * 10 means that child 2 is visible and child 1 is not.
     
    Now the shift of states means that some operations will performed, like
    '_add_child1' or '_remove_child2', these are mappend to ShiftPaned's
    methods.
    
    This means that if I'm changing from SHOW_CHILD1 to SHOW_CHILD2 I will have
    to remove child 2 ('_remove_child2') and add child 1 to the pane
    ('_add_child1'). Lets analize this mathmatically, the latter example means
    that we are changing from 01 to 10.
    
    Now for another example, from SHOW_CHILD2 to SHOW_BOTH, the change was from
    10 to 11 and we'll have to '_add_child1'.
    
    The conclusion about this is that when we shift from a 0 to a 1 we are
    infact adding the child on a given location, if it's the first bit we're
    adding child 1 if it's the second bit then we're adding child 2.
    But if we shift from a 1 to a 0 then we're removing a child from the pane.
    If the numbers are equal we do nothing.
    
    Now the implementation needs two things: the first is to get the visibility
    state from each child, these are the 'child1_oper' and 'child2_oper'
    lambda functions; the second function is something to convert the bit to
    an operation, this is fairly easy, subtracting a bit from the other we'll
    have three possible values:
     * 1 - 0: positive
     * 0 - 1: negative
     * 1 - 1 or 0 - 0: equal
    If we subtract the new bit from the old bit having a positive number means
    that we want to add something and a negative means that we want to remove
    it.
     
    """
    operations = []
    child1_oper = lambda state: state & SHOW_CHILD1
    child2_oper = lambda state: (state & SHOW_CHILD2) >> 1
    result = _state_to_operation(child1_oper(old_state), child1_oper(new_state))
    if result != None:
        operations.append(result + "1")
    
    result = _state_to_operation(child2_oper(old_state), child2_oper(new_state))
    if result != None:
        operations.append(result + "2")
    return operations

# fill _STATE_TO_WIDGET, it's faster to lookup then it is to calculate
_STATE_TO_WIDGET = {}

for old_state in range(4):
    for new_state in range(4):
        if old_state == new_state:
            continue
        _STATE_TO_WIDGET[(old_state, new_state)] = tuple(_get_operations(old_state, new_state))

# this is a forced memoize ;)
def _get_operations(old_state, new_state):
    global _STATE_TO_WIDGET
    return _STATE_TO_WIDGET[(old_state, new_state)]


class ShiftPaned(gtk.EventBox):
    """
    A ShiftPaned is a gtk.Paned that can hide one of its child widgets,
    therefore hiding the pane division.
    """
    _state = SHOW_BOTH
    _child1_args = ()
    _child1_kwargs = {}
    _child2_args = ()
    _child2_kwargs = {}
    child1_widget = None
    child2_widget = None
    
    def has_both_widgets(self):
        return self.child2_widget is not None and self.child1_widget is not None
    
    def __init__(self, paned_factory=gtk.HPaned):
        self.paned = paned_factory()
        self.paned.show()
        super(ShiftPaned, self).__init__()
        super(ShiftPaned, self).add(self.paned)
    
    def _add_child1(self):
        if self.child1_widget is not None and self.paned.get_child1() is None:
            self.paned.pack1(
                self.child1_widget,
                *self._child1_args,
                **self._child1_kwargs
            )

    def _add_child2(self):
        if self.child2_widget is not None and self.paned.get_child2() is None:
            self.paned.pack2(
                self.child2_widget,
                *self._child2_args,
                **self._child2_kwargs
            )
    
    def _remove_child1(self):
        if self.child1_widget is not None:
            self.paned.remove(self.child1_widget)
    
    def _remove_child2(self):
        if self.child2_widget is not None:
            self.paned.remove(self.child2_widget)
    
    def pack1(self, widget, *args, **kwargs):
        assert widget is not None
        self._child1_args = args
        self._child1_kwargs = kwargs
        self.child1_widget = widget
        if self._state & SHOW_CHILD1:
            self._add_child1()
    
    def pack2(self, widget, *args, **kwargs):
        assert widget is not None
        self._child2_args = args
        self._child2_kwargs = kwargs
        self.child2_widget = widget
        if self._state & SHOW_CHILD2:
            self._add_child2()
    
    def set_state(self, state):
        """This pane uses a number of states to act more effeciently the
        change of visibility of their children"""
        
        if state == self._state:
            return

        actions = _get_operations(self._state, state)
        get_method = lambda name: getattr(self, name)
        actions = map(get_method, actions)
        self._state = state
        for action in actions:
            action()
    

    def get_state(self):
        return self._state
    
    def show_child1(self):
        self.set_state(self._state | SHOW_CHILD1)
            
    def show_child2(self):
        self.set_state(self._state | SHOW_CHILD2)
    
    def hide_child1(self):
        self.set_state(self._state & ~SHOW_CHILD1)
    
    def hide_child2(self):
        self.set_state(self._state & ~SHOW_CHILD2)
    
    def get_child1_visibility(self):
        return (self._state & SHOW_CHILD1) == SHOW_CHILD1

    def get_child2_visibility(self):
        return (self._state & SHOW_CHILD2) == SHOW_CHILD2

    def set_position(self, position):
        self.paned.set_position(position)
    
    def get_position(self):
        return self.paned.get_position()

    def get_children(self):
        return self.paned.get_children()
    
    def remove(self, widget):
        if self.child1_widget is widget:
            self.child1_widget = None
        elif self.child2_widget is widget:
            self.child2_widget = None
        
        self.paned.remove(widget)
    
    def get_child1(self):
        return self.child1_widget
    
    def get_child2(self):
        return self.child2_widget
    
    def compute_position(self, *args, **kwargs):
        return self.paned.compute_position(*args, **kwargs)
    
    def add1(self, child):
        self.pack1(child)
    
    def add2(self, child):
        self.pack2(child)
    
    def add(self, widget):
        raise AttributeError("Use add1 and add2 instead.")


class SidebarPaned(gtk.EventBox):
    def __init__(self, paned_factory=gtk.HPaned, main_first=True):
        super(SidebarPaned, self).__init__()
        
        self.paned = ShiftPaned(paned_factory)
        self.main_first = main_first
        self.add(self.paned)
        self.paned.show()
    
    def pack_main(self, main_widget, *args, **kwargs):
        if self.main_first:
            self.paned.pack1(main_widget, *args, **kwargs)
        else:
            self.paned.pack2(main_widget, *args, **kwargs)
    
    def pack_sub(self, sub_widget, *args, **kwargs):
        if not self.main_first:
            self.paned.pack1(sub_widget, *args, **kwargs)
        else:
            self.paned.pack2(sub_widget, *args, **kwargs)
    
    def show_sub(self):
        # Faster this way
        self.paned.set_state(SHOW_BOTH)
    
    def hide_sub(self):
        if not self.main_first:
            self.paned.hide_child1()
        else:
            self.paned.hide_child2()
    
    def set_position(self, position):
        self.paned.set_position(position)

if __name__ == '__main__':
    #p = ShiftPaned(gtk.VPaned)
#    p = ShiftPaned(gtk.HPaned)
    p = SidebarPaned()
    
    btn1 = gtk.Button("Show sidebar")
    btn2 = gtk.Button("Hide sidebar")

    p.pack_main(btn1)
    p.pack_sub(btn2)
    
#    p.pack1(btn1)
#    p.pack2(btn2)

    def on_click(btn):
#        p.show_child2()
#        p.hide_child1()
        p.show_sub()
        
    btn1.connect("clicked", on_click)
    def on_click(btn):
#        p.show_child1()
#        p.hide_child2()
        p.hide_sub()
        
    btn2.connect("clicked", on_click)
    btn1.show()
    btn2.show()
    w = gtk.Window()
    vbox = gtk.VBox()
    vbox.add(p)
    w.add(vbox)
    w.show_all()
    w.connect("delete-event", gtk.main_quit)
    gtk.main()


