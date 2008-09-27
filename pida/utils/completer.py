# -*- coding: utf-8 -*- 

# Copyright (c) 2008 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import gtk
import gobject
import os
from const import UNKNOWN, ATTRIBUTE, CLASS, METHOD, MODULE, PROPERTY, \
    EXTRAMETHOD, VARIABLE, IMPORT

def _load_pix(fn):
    return gtk.gdk.pixbuf_new_from_file(
        os.path.join(os.path.dirname(__file__),
        "..","services","language","pixmaps", fn))


_PIXMAPS = {
    UNKNOWN:     _load_pix('element-event-16.png'),
    ATTRIBUTE:   _load_pix('source-attribute.png'),
    CLASS:       _load_pix('source-class.png'),
    METHOD:      _load_pix('source-attribute.png'),
    MODULE:      _load_pix('source-method.png'),
    PROPERTY:    _load_pix('source-property.png'),
    EXTRAMETHOD: _load_pix('source-extramethod.png'),
    VARIABLE:    _load_pix('element-event-16.png'),
    IMPORT:      _load_pix('source-import.png'),
}


class SuggestionsList(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf, str)

    @staticmethod
    def from_dbus(args):
        rv = list(args)
        if _PIXMAPS.has_key(args[0]):
            rv[0] = _PIXMAPS[args[0]]
        else:
            rv[0] = _PIXMAPS[UNKNOWN]
        return rv

class PidaCompleterWindow(gtk.Window):
    def __init__(self, type_=gtk.WINDOW_TOPLEVEL):
        super(PidaCompleterWindow, self).__init__(type_)
        self.widget = PidaCompleter()
        self.add(self.widget)
        self.set_decorated(False)



class PidaCompleter(gtk.HBox):

    __gsignals__ = {
        "user-abort" :   (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE, 
                          (gobject.TYPE_STRING,)),
        "user-accept" :   (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE, 
                          (gobject.TYPE_STRING,)),
        "suggestion-selected" :   (gobject.SIGNAL_RUN_LAST, 
                                   gobject.TYPE_NONE, 
                                  (gobject.TYPE_STRING,)),
    }



    def __init__(self, show_input=True, show_icons=True,
                 filter_=""):
        self._model = None
        super(PidaCompleter, self).__init__()
        self._show_input = show_input
        self._filter = ''
        self._create_ui()
        self._ignore_change = False
        self.show_icons = show_icons
        
        #self._tree.set_model(SuggestionsTree())
        self.filter = filter_
        
        self._tree.connect("row-activated", self.on_row_activated)
        
        if show_input:
            self._entry.connect('key-press-event', self.on_key_press_event)
            self._entry.grab_focus()
        
        # public vars

        # ignore case does case insensetive filter
        self.ignore_case = True
        # tab
        self.accept_keys = (65289,)
        # esc
        self.abort_keys = (65307,)

    def filter_function(self, model, iter_):
        if not self._filter:
            return True
        if self.ignore_case:
            var = self._modelreal.get_value(iter_, 1)
            if var: var = var.lower()
            filter_ = self._filter.lower()
        else:
            var = self._modelreal.get_value(iter_, 1)
            filter_ = self._filter
        if not var:
            return False
        if var[:len(self._filter)] == filter_:
                return True
        return False

    def on_entry_changed(self, widget, *args):
        if self._ignore_change:
            return True
        self._filter = self._get_non_sel() #widget.get_text()
        if self._model: self._model.refilter()

    def on_row_activated(self, treeview, path, view_column):
        self._sig_clean("user-accept", self._modelreal[path[0]][1])

    def _sig_clean(self, sig, val):
        self.emit(sig, val)
        self._filter = ''
        self.hide()

    def _update_sel(self, new_text):
        text = self._get_non_sel()
        self._ignore_change = True
        #print "non sel", text, new_text
        #print text + new_text[len(text):]
        op = self._entry.get_position()
        nt = new_text
        self._entry.set_text(nt)
        self._entry.set_position(op)
        self._entry.select_region(len(nt),op)
        self._ignore_change = False
        self.emit("suggestion-selected", nt)

    def _get_non_sel(self):
        sel = self._entry.get_selection_bounds()
        if not sel:
            return self._entry.get_text()
        return self._entry.get_text()[:sel[0]]

    def on_key_press_event(self, widget, event):
        if event.type == gtk.gdk.KEY_PRESS:
            print "key_pressed ", event.keyval
            #tab 65289
            if event.keyval in self.accept_keys:
                self._sig_clean("user-accept", self._filter)
                return True
            elif event.keyval in self.abort_keys:
                self._sig_clean("user-abort", self._filter)
                return True
            elif event.keyval in (65366, 65365):
                # FIXME: pageup/down
                pass
            elif event.keyval == 65364: #key down
                s = self._tree.get_selection()
                it = s.get_selected()[1]
                if not it:
                    ni = self._model.get_iter_first()
                else:
                    ni = self._model.iter_next(it)
                if not ni:
                    return True
                s.select_iter(ni)
                self._tree.scroll_to_cell(self._model.get_path(ni))
                nt = self._model.get_value(ni, 1)
                self._update_sel(nt)
                return True
            elif event.keyval == 65362: #key up
                s = self._tree.get_selection()
                it = s.get_selected()[1]
                print it
                if not it:
                    return True
                path = self._model.get_path(it)
                if path[0] == 0:
                    return True
                np = (path[0]-1,)
                s.select_path(np)
                self._tree.scroll_to_cell(np, use_align=False, row_align=0.0, col_align=0.0)
                print self.filter
                nt = self._model.get_value(self._model.get_iter(np), 1)
                self._update_sel(nt)
                #ov = self._entry.get_text()
                #self._entry.set_text(nt)
                #self._entry.select_region(
                #self._entry.set_inline_completion(inline_completion)
                return True
            elif event.keyval == 65293: # enter
                self._sig_clean("user-accept", self._entry.get_text())
                return True
                #pass
            else:
                return
                # 
                #if event.string:
                # we pass the event to the entry box so it can handle
                # the key events like a normal entry box
                return
    
    #@property
    def get_model(self):
        return self._model
    
    def set_model(self, model):
        #model = gtk.(gobject.TYPE_INT, gobject.TYPE_STRING)
        #self._tree.set_model(model)
        self._modelreal = model
        self._model = model.filter_new()
        self._model.set_visible_func(self.filter_function)
        self._tree.set_model(self._model)

        #return self._tree.get_model()
    model = property(get_model, set_model)
        
    def get_filter(self):
        """
        The filter is used to increate completion speed
        """
        return self._entry.get_text()
        
    def set_filter(self, value, update_field=True):
        self._filter = value
        if update_field:
            self._entry.set_text(value)
        if self._model: self._model.refilter()
        #self._model.
        
    filter = property(get_filter, set_filter)
    
    def _create_ui(self):
        self._box = gtk.VBox()
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        #self._box = scrolled_window
        #self.add(scrolled_window)
        self.set_size_request(150, 300)
        #self.set_decorated(False)
        self._entry = gtk.Entry()
        #self._entry.connect("insert-text", self.on_entry_changed)
        #self._entry.connect("delete-text", self.on_entry_changed)
        self._entry.connect("changed", self.on_entry_changed)
        #self._entry.set_text(self.filter)
        if self._show_input:
            self._box.pack_start(self._entry, False, False)
        #self._entry.set_size_request(0, 0)
        self._tree = gtk.TreeView()
        self._tree.set_size_request(100, 100)
        self._tree.set_headers_visible(False)
        self._tree.set_enable_search(False)
        #self._tree.set_fixed_height_mode(True)
        self._tree_icons = ic = gtk.TreeViewColumn('Typ', gtk.CellRendererPixbuf(), pixbuf=0)
        ic.set_visible(self.show_icons)
        ic.set_resizable(False)
        ic.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        ic.set_fixed_width(32)
        ic.set_reorderable(False)
        self._tree.append_column(ic)
        self._tree_label = ic = gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1)
        ic.set_resizable(True)
        ic.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        #ic.set_fixed_width(32)
        ic.set_reorderable(False)
        self._tree.append_column(ic)
        scrolled_window.add(self._tree)
        self._box.add(scrolled_window)
        self.add(self._box)
        self.show_all()
        self.hide()

    def get_show_icons(self):
        return self._tree_icons.get_visible()

    def set_show_icons(self, value):
        return self._tree_icons.set_visible(value)
        
    def add_str(self, line):
        self._modelreal.append((None, line))

    show_icons = property(get_show_icons, set_show_icons)

gobject.type_register(PidaCompleter)

if __name__ == "__main__":
    def accepted(*args):
        print "user accepted ", args

    def abort(*args):
        print "user abort ", args

    w = PidaCompleterWindow()#gtk.WINDOW_POPUP)
    p = w.widget
    l = SuggestionsList()

    i = 0
    for x in ['ase', 'assdf', 'Asdf', 'zasd', 'Zase', 'form', 'in', 'of', 'BLA',
              'taT', 'tUt', 'df', 'asdf', 'asdfa', 'sd', 'sdfsf', 'ssdfsdf', 'sd']:
        l.append(SuggestionsList.from_dbus((i, x)))
        i = i + 1%7

    p.set_model(l)

    p.connect("user-abort", abort)
    p.connect("user-accept", accepted)

    w.show_all()
    w.grab_focus()
    gtk.main()