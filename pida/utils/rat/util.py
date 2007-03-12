__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"
__doc__ = """
This module contains usefull functions like widget navigation and
list store creation.
"""

import gtk

class NotFoundError(KeyError):
    """This is raised when an element is not found"""

class ListSpec:
    """
    This class is used to help the manipulation of C{gtk.ListStore}s.
    Here's an example on how to create one::

        my_spec = ListSpec(
            ("STATE", gobject.TYPE_INT),
            ("FILENAME", gobject.TYPE_STRING),
        )
    
    To create a ListStore, just do the following::
    
        store = my_spec.create_list_store()
    
    To add data to a store you can access it directly::
    
        store.append((1, "fooo"))
    
    Or by creating a dict object and converting it::
        
        row = {
            my_spec.STATE: 2,
            my_spec.FILENAME: "bar"
        }
        store.append(my_spec.to_tree_row(row))
        
    To access a column on a given row::
    
        for row in store:
            print "State:", row[my_spec.STATE]
            print "Filename:", row[my_spec.FILENAME]
    
    So here are its features:
     - helps you centralize the specs of a given C{gtk.ListStore}
     - makes your code more readable and less error-prone thanks to the
       created constants
       
    """
    def __init__(self, *columns):
        names = []
        gtypes = []
        
        for(index,(name, gtype)) in enumerate(columns):
            assert name != "create_list_store" and name != "to_tree_row"
            
            setattr(self, name, index)
            gtypes.append(gtype)
            
        self.__gtypes = tuple(gtypes)
        
    def create_list_store(self):
        """Creates a new C{gtk.ListStore}
        @rtype: C{gtk.ListStore}
        """
        return gtk.ListStore(*self.__gtypes)
    
    def to_tree_row(self, mapping):
        """
        Converts a L{dict} like object to a list suitable for adding to a 
        C{gtk.ListStore}.
        
        @rtype: C{ListType}
        """
        keys = mapping.keys()
        keys.sort()
        return [mapping[key] for key in keys]

################################################################################
# widget iterators
def _simple_iterate_widget_children(widget):
    """This function iterates all over the widget children.
    """
    get_children = getattr(widget, "get_children", None)

    if get_children is None:
        return
    
    for child in get_children():
        yield child

    get_submenu = getattr(widget, "get_submenu", None)
    
    if get_submenu is None:
        return
    
    sub_menu = get_submenu()
    
    if sub_menu is not None:
        yield sub_menu

class _IterateWidgetChildren:
    """This iterator class is used to recurse to child widgets, it uses
    the _simple_iterate_widget_children function
    
    """
    def __init__(self, widget):
        self.widget = widget
        self.children_widgets = iter(_simple_iterate_widget_children(self.widget))
        self.next_iter = None
        
    def next(self):
        if self.next_iter is None:
            widget = self.children_widgets.next()
            self.next_iter = _IterateWidgetChildren(widget)
            return widget
            
        else:
            try:
                return self.next_iter.next()
            except StopIteration:
                self.next_iter = None
                return self.next()

    def __iter__(self):
        return self
        
def iterate_widget_children(widget, recurse_children = False):
    """
    This function is used to iterate over the children of a given widget.
    You can recurse to all the widgets contained in a certain widget.
    
    @param widget: The base widget of iteration
    @param recurse_children: Wether or not to iterate recursively, by iterating
        over the children's children.
    
    @return: an iterator
    @rtype: C{GeneratorType}
    """
    if recurse_children:
        return _IterateWidgetChildren(widget)
    else:
        return iter(_simple_iterate_widget_children(widget))

def iterate_widget_parents(widget):
    """Iterate over the widget's parents.

    @param widget: The base widget of iteration
    @return: an iterator
    @rtype: C{GeneratorType}
    """
    
    widget = widget.get_parent()
    while widget is not None:
        yield widget
        widget = widget.get_parent()

def find_parent_widget(widget, name, find_self=True):
    """
    Finds a widget by name upwards the tree, by searching self and its parents
    
    @return: C{None} when it didn't find it, otherwise a C{gtk.Container}
    @rtype: C{gtk.Container}
    @param find_self: Set this to C{False} if you want to only find on the parents
    @param name: The name of the widget
    @param widget: The widget where this function will start searching
    """
    
    assert widget is not None

    if find_self and widget.get_name() == name:
        return widget

    for w in iterate_widget_parents(widget):
        if w.get_name() == name:
            return w

    raise NotFoundError(name)

def find_child_widget(widget, name, find_self=True):
    """
    Finds the widget by name downwards the tree, by searching self and its
    children.

    @return: C{None} when it didn't find it, otherwise a C{gtk.Widget}
    @rtype: C{gtk.Widget}
    @param find_self: Set this to L{False} if you want to only find on the children
    @param name: The name of the widget
    @param widget: The widget where this function will start searching
    """
    
    assert widget is not None
    
    if find_self and widget.get_name() == name:
        return widget
    
    for w in iterate_widget_children(widget, True):

        if name == w.get_name():
            return w
    
    raise NotFoundError(name)

        

def get_root_parent(widget):
    """Returns the first widget of a tree. If this widget has no children
    it will return C{None}
    
    @return: C{None} when there is no parent widget, otherwise a C{gtk.Container}
    @rtype: C{gtk.Container} 
    """
    parents = list(iterate_widget_parents(widget))
    if len(parents) == 0:
        return None
    else:
        return parents[-1]

