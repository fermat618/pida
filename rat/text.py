"""
This module contains to, very usefull utility functions, one for grabbing
the text selected on a certain `gtk.TreeBuffer`, the other creates an iterator
for manipulating searches to a `gtk.TreeBuffer`.
"""
__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import gtk

def get_buffer_selection(buffer):
    """Returns the selected text, when nothing is selected it returns the empty
    string."""
    bounds = buffer.get_selection_bounds()
    if len(bounds) == 0:
        return ""
    else:
        return buffer.get_slice(*bounds)

class SearchIterator:
    def __init__(self, text_buffer, search_text, find_forward=True, start_in_cursor=True, next_iter=None):
        self.search_text = search_text
        self.text_buffer = text_buffer
        self.find_forward = find_forward
        
        if next_iter is not None:
            self.next_iter = next_iter
        
        elif start_in_cursor:
            bounds = text_buffer.get_selection_bounds()
            if len(bounds) == 0:
                self.next_iter = text_buffer.get_iter_at_mark(text_buffer.get_insert())
            else:
                self.next_iter = find_forward and bounds[1] or bounds[0]
        
        else:
            if find_forward:
                self.next_iter = text_buffer.get_start_iter()
            else:
                self.next_iter = text_buffer.get_end_iter()
        
        
        
    def next(self):
        if self.next_iter is None:
            raise StopIteration
        
        find_forward = self.find_forward
        
        if find_forward:
            search = self.next_iter.forward_search
        else:
            search = self.next_iter.backward_search
            
        bounds = search(self.search_text, gtk.TEXT_SEARCH_TEXT_ONLY, limit=None)
        
        if bounds is None:
            self.next_iter = None
            raise StopIteration
        
        if find_forward:
            self.next_iter = bounds[1]
        else:
            self.next_iter = bounds[0]
        
        return bounds
    
    def __iter__(self):
        return self
        
search_iterator = SearchIterator

def line_iterator(buff, start_iter, end_iter):
    begin_line = start_iter.get_line()
    end_line = end_iter.get_line()
    assert begin_line <= end_line
    for line_num in range(begin_line, end_line+1):
        yield buff.get_iter_at_line(line_num)

def selected_line_iterator(buff):
    """
    Iterates over selected lines
    """
    bounds = buff.get_selection_bounds()
    if len(bounds) == 0:
        return
    last_iter = bounds[1]
    
    for start_iter in line_iterator(buff, *bounds):
        # Skip empty lines
        if start_iter.equal(last_iter) or start_iter.ends_line():
            continue
        yield start_iter

def indent_selected(buff, indent):
    """
    Indents selected text of a gtk.TextBuffer
    """
    
    bounds = buff.get_selection_bounds()
    if len(bounds) == 0:
        return

    move_home = bounds[0].starts_line()
    
    insert = buff.insert
    insert_indent = lambda start_iter: insert(start_iter, indent)
    map(insert_indent, selected_line_iterator(buff))
    
    if move_home:
        start_iter, end_iter = buff.get_selection_bounds()
        start_iter.set_line_offset(0)
        buff.select_range(end_iter, start_iter)
    
    
def _unindent_iter(buff, start_iter, indent, use_subset):
    # Get the iterator of the end of the text
    end_iter = start_iter.copy()
    end_iter.forward_to_line_end()
    total = len(indent)
    
    # Now get the selected text
    text = buff.get_text(start_iter, end_iter)
    
    # Check if the text starts with indent:
    if text.startswith(indent):
        count = total
        # Delete 'count' characters
        end_iter = start_iter.copy()
        end_iter.forward_chars(count)
        buff.delete(start_iter, end_iter)

    elif use_subset:
        for count in range(1, total):
            if text.startswith(indent[:-count]):
                # Delete 'count' characters
                offset = total - count
                end_iter = start_iter.copy()
                end_iter.forward_chars(offset)
                buff.delete(start_iter, end_iter)
                return


def unindent_selected(buff, indent, use_subset=True):
    """
    Unindents selected text of a `gtk.TextBuffer` 
    """
    if len(buff.get_selection_bounds()) == 0:
        start_iter = buff.get_iter_at_mark(buff.get_insert())
        # Move the offset to the start of the line
        start_iter.set_line_offset(0)
        _unindent_iter(buff, start_iter, indent, use_subset)
        end_iter = start_iter.copy()
        end_iter.forward_to_line_end()
        
    unindent_iter = lambda start_iter: _unindent_iter(buff, start_iter, indent, use_subset)
    map(unindent_iter, selected_line_iterator(buff))

# This function belongs to make_soruce_view_indentable
def _on_key_press(view, event):
    keyname = gtk.gdk.keyval_name(event.keyval)
    buff = view.get_buffer()
    
    if view.get_insert_spaces_instead_of_tabs():
        tab = " " * view.get_tabs_width()
    else:
        tab = "\t"

    if event.state & gtk.gdk.SHIFT_MASK and keyname == "ISO_Left_Tab":
        unindent_selected(buff, tab)
        return True
        
    elif event.keyval == gtk.keysyms.Tab:
        if len(buff.get_selection_bounds()) == 0:
            return False
        indent_selected(buff, tab)
        return True



def make_source_view_indentable(source_view):
    # TODO: make the selection carret move to the end of the selection
    # and not the start
    return source_view.connect("key-press-event", _on_key_press)

