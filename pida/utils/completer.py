# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import gobject
import os
from languages import LANG_COMPLETER_TYPES

def _load_pix(fn):
    return gtk.gdk.pixbuf_new_from_file(
        os.path.join(os.path.dirname(__file__),
        "..","services","language","pixmaps", fn))


_PIXMAPS = {
    LANG_COMPLETER_TYPES.UNKNOWN:     _load_pix('element-event-16.png'),
    LANG_COMPLETER_TYPES.ATTRIBUTE:   _load_pix('source-attribute.png'),
    LANG_COMPLETER_TYPES.CLASS:       _load_pix('source-class.png'),
    LANG_COMPLETER_TYPES.FUNCTION:    _load_pix('source-attribute.png'), # FIXME
    LANG_COMPLETER_TYPES.METHOD:      _load_pix('source-attribute.png'),
    LANG_COMPLETER_TYPES.MODULE:      _load_pix('source-method.png'),
    LANG_COMPLETER_TYPES.PROPERTY:    _load_pix('source-property.png'),
    LANG_COMPLETER_TYPES.EXTRAMETHOD: _load_pix('source-extramethod.png'),
    LANG_COMPLETER_TYPES.VARIABLE:    _load_pix('source-attribute.png'), # FIXME
    LANG_COMPLETER_TYPES.IMPORT:      _load_pix('source-import.png'),
    LANG_COMPLETER_TYPES.PARAMETER:   _load_pix('source-attribute.png'), # FIXME
    LANG_COMPLETER_TYPES.BUILTIN:     _load_pix('source-attribute.png'), # FIXME
    LANG_COMPLETER_TYPES.KEYWORD:     _load_pix('source-attribute.png'), # FIXME
}


class SuggestionsList(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf, str)

    @staticmethod
    def from_dbus(args):
        rv = list(args)
        if args[0] in _PIXMAPS:
            rv[0] = _PIXMAPS[args[0]]
        else:
            rv[0] = _PIXMAPS[LANG_COMPLETER_TYPES.UNKNOWN]
        return rv

class PidaCompleterWindow(gtk.Window):
    def __init__(self, type_=gtk.WINDOW_TOPLEVEL, 
                    show_input=True, show_icons=True):
        super(PidaCompleterWindow, self).__init__(type_)
        self.set_focus_on_map(False)
        self.widget = PidaCompleter(show_input=show_input, show_icons=show_icons)
        self.add(self.widget)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_role('completer')
        self.set_property('accept-focus', False)
        self.set_property('skip-pager-hint', True)
        self.set_property('skip-taskbar-hint', True)
        self.set_property('type-hint', gtk.gdk.WINDOW_TYPE_HINT_TOOLTIP)




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
        self.min_height = 130
        self.max_height = 400
        self.min_width = 200
        self.max_width = 500
        
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
            #print "key_pressed ", event.keyval
            #tab 65289
            if event.keyval in self.accept_keys:
                self._sig_clean("user-accept", self._filter)
                return True
            elif event.keyval in self.abort_keys:
                self._sig_clean("user-abort", self._filter)
                return True
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
                if not it:
                    return True
                path = self._model.get_path(it)
                if path[0] == 0:
                    return True
                np = (path[0]-1,)
                s.select_path(np)
                self._tree.scroll_to_cell(np, use_align=False, row_align=0.0, col_align=0.0)
                nt = self._model.get_value(self._model.get_iter(np), 1)
                self._update_sel(nt)
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Page_Up'):
                s = self._tree.get_selection()
                vr = self._tree.get_visible_range()
                diff = vr[1][0]-vr[0][0]
                np = (max(vr[0][0]-diff,0),)
                s.select_path(np)
                self._tree.scroll_to_cell(np, use_align=False, row_align=0.0, col_align=0.0)
                nt = self._model.get_value(self._model.get_iter(np), 1)
                self._update_sel(nt)
                return True
                
            elif event.keyval == gtk.gdk.keyval_from_name('Page_Down'):
                s = self._tree.get_selection()
                vr = self._tree.get_visible_range()
                diff = vr[1][0]-vr[0][0]
                np = (vr[0][0]+diff,)
                s.select_path(np)
                self._tree.scroll_to_cell(np, use_align=True, row_align=0.0, col_align=0.0)
                nt = self._model.get_value(self._model.get_iter(np), 1)
                self._update_sel(nt)
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

    def __len__(self):
        return len(self._modelreal)

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
        #self.set_size_request(150, 300)
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
        #self._tree.set_size_request(100, 100)
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

    def place(self, x, y, height, below=True):
        """
        Try to place the completer optimal on the window.
        x, y is top left corner of the position the window should be placed
        and height the hight of the line.The line will not be overlapped.
        """
        swid = gtk.gdk.screen_width()
        shei = gtk.gdk.screen_height()

        BELOW = 1
        ABOVE = 2

        pos = below and BELOW or ABOVE

        tar_x, tar_y = 0, 0
        tar_height, tar_widht = self.max_height, self.min_width

        if self.min_height + height + y > shei:
            pos = ABOVE

        if pos == ABOVE and y - self.min_height < 0:
            pos = BELOW

        if pos == BELOW:
            tar_x = x 
            tar_y = y + height
            tar_height = min(shei - y - height, tar_height)
        else:
            tar_height = min(y, tar_height)
            tar_x = x
            tar_y = y - tar_height

        self.parent.set_size_request(tar_widht, tar_height)
        self.parent.resize(tar_widht, tar_height)
        self.parent.move(tar_x, tar_y)


    def get_show_icons(self):
        return self._tree_icons.get_visible()

    def set_show_icons(self, value):
        return self._tree_icons.set_visible(value)

    def add_str(self, line, type_=None):
        # we only hold a uniqe list of items
        # because a later suggestion may give us a better type, we update the
        # old one
        for entry in self._modelreal:
            if entry[1] == line:
                if entry[0] == None:
                   entry[0] = _PIXMAPS.get(type_, None)
                return

        self._modelreal.append((_PIXMAPS.get(type_, None), line))

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
#     gtk.rc_parse('/home/poelzi/Projects/pida/loadfix/pida/resources/data/gtkrc-2.0')
#     pw = PidaDocWindow(
#     'bla.blubb',
#     'some small info', 
#     '''this is a long
#     text and more info
#     more bla bla and something
#     * blubb
#     ''')
#     pw.present()

    gtk.main()
