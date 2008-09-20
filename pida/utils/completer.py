import gtk
import gobject
import os

def _load_pix(fn):
    return gtk.gdk.pixbuf_new_from_file(
        os.path.join(os.path.dirname(__file__),
        "..","services","language","pixmaps", fn))

UNKNOWN = 0, 
ATTRIBUTE = 1
CLASS = 2
METHOD = 3
MODULE = 4
PROPERTY = 5
EXTRAMETHOD = 6
VARIABLE = 7
IMPORT = 8


pixis = {
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
        gtk.ListStore.__init__(self, int, str)
        

class TypeRenderer(gtk.CellRendererPixbuf):
    """
    We use a special type renderer so we don't have to store the
    pixbuffer images in the tree
    """
    __gproperties__ = {
           'entrytyp' : (gobject.TYPE_INT,                        # type
                     'type of entry',                         # nick name
                     'number of pixmap to display', # description
                     0,                                         # minimum value
                     99,                                        # maximum value
                     0,                                        # default value
                     gobject.PARAM_READWRITE)                   # flags
    }
    
    def __init__(self, *args, **kwargs):
        gtk.CellRendererPixbuf.__init__(self, *args, **kwargs)
        self._typ = 0
    
    def do_set_property(self, prop, value):
        if prop.name == 'entrytyp':
            if pixis.has_key(value):
                self.set_property('pixbuf', pixis[value])

    def do_get_property(self, name, value):
        if name == 'entrytyp':
            return self._typ

gobject.type_register(TypeRenderer)

class PidaCompleter(gtk.Window):

    __gsignals__ = {
        "user-abort" :   (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE, 
                          (gobject.TYPE_STRING,)),
        "user-accept" :   (gobject.SIGNAL_RUN_LAST, 
                          gobject.TYPE_NONE, 
                          (gobject.TYPE_STRING,)),
    }



    def __init__(self, show_input=True, show_icons=True,
                 filter_=""):
        self._model = None
        super(PidaCompleter, self).__init__()
        self._show_input = show_input
        self._filter = ''
        print self
        self._create_ui()
        
        #self._tree.set_model(SuggestionsTree())
        self.filter = filter_
        
        self._tree.connect("row-activated", self.on_row_activated)
        
        if show_input:
            self._entry.connect('key-press-event', self.on_key_press_event)
            self._entry.grab_focus()
        
        # public vars

        # ignore case does case insensetive filter
        self.ignore_case = False
        # tab
        self.accept_keys = (65289,)
        # esc
        self.abort_keys = (65307,)
    
    def filter_function(self, model, iter_):
        if not self._filter:
            return True
        if self.ignore_case:
            var = self._modelreal.get_value(iter_, 1).lower()
            filter_ = self._filter.lower()
        else:
            var = self._modelreal.get_value(iter_, 1)
            filter_ = self._filter
        if var[:len(self._filter)] == filter_:
                return True
        return False

    def on_entry_changed(self, widget):
        self.filter = widget.get_text()

    def on_row_activated(self, treeview, path, view_column):
        self._sig_clean("user-accept", self._modelreal[path[0]][1])

    def _sig_clean(self, sig, val):
        self.emit(sig, val)
        self._filter = ''
        self.hide()
    

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
            else:
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
        self.set_decorated(False)
        self._entry = gtk.Entry()
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
        ic = gtk.TreeViewColumn('Typ', TypeRenderer(), entrytyp=0)
        ic.set_resizable(False)
        ic.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        ic.set_fixed_width(32)
        ic.set_reorderable(False)
        self._tree.append_column(ic)
        ic = gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1)
        ic.set_resizable(True)
        ic.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        #ic.set_fixed_width(32)
        ic.set_reorderable(False)
        self._tree.append_column(ic)
        scrolled_window.add(self._tree)
        self._box.add(scrolled_window)
        self.add(self._box)
        
        
gobject.type_register(PidaCompleter)
        
if __name__ == "__main__":
    def accepted(*args):
        print "user accepted ", args
        
    def abort(*args):
        print "user abort ", args
        
    p = PidaCompleter()
    l = SuggestionsList()
    
    i = 0
    for x in ['ase', 'assdf', 'Asdf', 'zasd', 'Zase', 'form', 'in', 'of', 'BLA',
              'taT', 'tUt']:
        l.append((i, x))
        i = i + 1%7

    p.set_model(l)
    
    p.connect("user-abort", abort)
    p.connect("user-accept", accepted)
    
    p.show_all()
    gtk.main()