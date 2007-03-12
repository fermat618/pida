__doc__ = """
The HIG module offers a set of utility functions and widgets to implement
HIG compliant interfaces.

This module defines a pipeline of costumizing widgets, it follows the simple
procedure that creating a HIG compliant application can be thought of a
work that has patterns of costumizations that act in different levels with
different widgets, we'll address them as Costumizers.

To call a dialog for asking the user to save changes on a certain file use this::

    >>> import rat.hig
    >>> rat.hig.save_changes(["foo.bar", "foo"], title = "Save changes?")
    (['foo.bar'], -6)

There are also utility functions for calling dialogs, like warning messages::

    >>> rat.hig.dialog_warn("Rat will simplify your code",
    ...                  "By putting common utilities in one place makes all "
    ...                  "benefit and get nicer apps.")
    -5

Sometimes you want to manipulate the dialog before running it::

    >>> rat.hig.dialog_warn("Rat will simplify your code",
    ...                  "By putting common utilities in one place makes all "
    ...                  "benefit and get nicer apps.", run = False)
    <gtk.Dialog object(GtkDialog) at 0xb73a19b4>

"""
__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import gobject
import gtk
import datetime
from util import find_child_widget

from gettext import gettext as _
from gettext import ngettext as N_


class WidgetCostumizer:
    """
    The WidgetCostumizer is a class template for defining chaining of asseblies
    of interfaces. For example you can create a dialog with this simple lines of
    code::
    
        creator.bind(SetupDialog()).bind(SetupAlert(primary_text, secondary_text, **kwargs))
        dlg = creator()
    
    The costumization of a widget is like a pipeline of filters that act on a
    certain widget and on a toplevel container.
    
    """
    _to_attrs = True
    _defaults = {}
    _next_values = None
    _next_iter = None
    
    def __init__(self, *args, **kwargs):
        self._args  = args
        self._kwargs = dict(self._defaults)
        self._kwargs.update(kwargs)
        self._next_values = []
    
    def _get_next(self):
        return self._next_iter.next()
    
    def update(self, **kwargs):
        self._kwargs.update(kwargs)
    
    def _run(self, *args, **kwargs):
        pass
    
    def bind(self, *others):
        for other in others:
            if not isinstance(other, WidgetCostumizer):
                raise TypeError(type(other))
            
            self._next_values.append(other)

        return self
    
    def _call(self, widget, container):
        if self._to_attrs:
            for key, value in self._kwargs.iteritems():
                setattr(self, key, value)
            
        widget, container = self._run(widget, container)
        
        for costum in self._next_values:
            widget, container = costum._call(widget, container)
        
        for key in self._kwargs:
            delattr(self, key)
        return widget, container
        
    def __call__(self, widget = None, container = None):
        """This method is only called once"""
        return self._call(widget, container)[0]

class SetupScrolledWindow(WidgetCostumizer):
    def _run(self, scrolled, container):
        assert container is None

        if scrolled is None:
            scrolled = gtk.ScrolledWindow()
        
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        return scrolled, None
        
class SetupLabel(WidgetCostumizer):
    """
    Usage::

        lbl = SetupLabel("<b>foo</b>")(gtk.Label())
        lbl.show()
        
    Or::
    
        lbl = SetupLabel("<b>foo</b>")()
        lbl.show()
    
    """
    def _run(self, lbl, container):
        assert container is None
        assert len(self._args) == 0 or len(self._args) == 1
        
        if lbl is None:
            lbl = gtk.Label()
            
        lbl.set_alignment(0, 0)
        
        if len(self._args) == 1:
            lbl.set_markup(self._args[0])
            
        lbl.set_selectable(True)
        lbl.set_line_wrap(True)
        
        return lbl, container
            
def _dialog_decorator(func):
    def wrapper(self, dialog, container):
        if container is None:
            container = dialog.get_child()
        return func(self, dialog, container)
        
    return wrapper

class SetupDialog(WidgetCostumizer):
    def _run(self, dialog, container):
        dialog.set_border_width(4)
        dialog.set_has_separator(False)
        dialog.set_title("")
        dialog.set_resizable(False)

        align = gtk.Alignment()
        align.set_padding(
            padding_top = 0,
            padding_bottom = 7,
            padding_left = 0,
            padding_right = 0
        )
        align.set_border_width(5)
        align.show()
        container.add(align)
        
        return dialog, align
    
    _run = _dialog_decorator(_run)


class SetupAlert(WidgetCostumizer):
    class _PrimaryTextDecorator:
        def __init__(self, label):
            self.label = label
            
        def __call__(self, primary_text):
            self.label.set_markup(
                '<span weight="bold" size="larger">'+primary_text+'</span>'
            )
        
            
    _defaults = {
        "title": "",
        "stock": gtk.STOCK_DIALOG_INFO
    }
    
    def _before_text(self, dialog, vbox):
        pass
    
    def _after_text(self, dialog, vbox):
        pass
    
    def _run(self, dialog, container):
        primary_text, secondary_text = self._args

        dialog.set_title(self.title)

        hbox = gtk.HBox(spacing = 12)
        hbox.set_border_width(0)
        hbox.show()
        container.add(hbox)
        
        img = gtk.Image()
        img.set_from_stock(self.stock, gtk.ICON_SIZE_DIALOG)
        img.set_alignment(img.get_alignment()[0], 0.0)
        img.show()
        hbox.pack_start(img, False, False)
        
        vbox = gtk.VBox(spacing = 6)
        vbox.show()
        hbox.pack_start(vbox)
        
        
        lbl = SetupLabel(
            '<span weight="bold" size="larger">'+primary_text+'</span>'
        )()
        lbl.show()
        
        
        dialog.set_primary_text = self._PrimaryTextDecorator(lbl)
        
        vbox.pack_start(lbl, False, False)
        
        lbl = SetupLabel(secondary_text)()
        lbl.show()
        dialog.set_secondary_text = lbl.set_text
        
        def on_destroy(widget):
            delattr(widget, "set_secondary_text")
            delattr(widget, "set_primary_text")
        
        dialog.connect("destroy", on_destroy)
        
        self._before_text(dialog, vbox)
        vbox.pack_start(lbl, False, False)
        self._after_text(dialog, vbox)
        
        return dialog, vbox

    _run = _dialog_decorator(_run)


class _SetupRadioChoiceList(SetupAlert):
    
    def _after_text(self, dialog, container):
        vbox = gtk.VBox(spacing=6)
        vbox.show()
        vbox.set_name("items")
        
        container.pack_start(vbox)
        group = None
        for item in self.items:
            radio = gtk.RadioButton(group, item)
            radio.show()
            
            if group is None:
                group = radio
            
            vbox.pack_start(radio, False, False)
            
class SetupListAlertTemplate(SetupAlert):
    def get_list_title(self):
        raise NotImplementedError
    
    def configure_widgets(self, dialog, tree):
        raise NotImplementedError

    def create_store(self):
        raise NotImplementedError
    
    def _before_text(self, dialog, vbox):
        store = self.create_store()
        
        title = self.get_list_title()
        
        if title is not None:
            lbl = SetupLabel(title)()
            lbl.show()
            vbox.pack_start(lbl, False, False)
        
        tree = gtk.TreeView()
        tree.set_name("list_view")
        tree.set_model(store)
        tree.set_headers_visible(False)

        tree.show()
        scroll = SetupScrolledWindow()()
        scroll.add(tree)
        scroll.show()
        scroll.set_name("scrolled_window")
        
        vbox.add(scroll)

        self.configure_widgets(dialog, tree)
        count = len(tree.get_model())
        # Update the size according to the number of elements on the list
        if count > 5:
            scroll.set_size_request(-1, min(154, 30 * count / 2))
        return dialog, vbox

class _SetupMultipleChoiceList(SetupListAlertTemplate):

    _defaults = {
        "list_title": None
    }
    _defaults.update(SetupAlert._defaults)

    def get_list_title(self):
        return self.list_title

    def configure_widgets(self, dialog, tree):
        store = tree.get_model()
        
        
        # Create the callback
        def on_toggle(render, path, args):
            dialog, model, min_sel, max_sel = args
            
            tree_iter = model.get_iter(path)
            row = model[tree_iter]
            row[0] = not row[0]
            
            if row[0]:
                model.enabled_rows += 1
            else:
                model.enabled_rows -= 1
            
            if model.enabled_rows == 0:
                is_sensitive = False
            elif max_sel >= 0:
                is_sensitive = min_sel <= model.enabled_rows <= max_sel
            else:
                is_sensitive = min_sel <= model.enabled_rows
            
            dialog.set_response_sensitive(gtk.RESPONSE_OK, is_sensitive)
        
        args = (dialog, store, self.min_select, self.max_select)

        rend = gtk.CellRendererToggle()
        rend.connect("toggled", on_toggle, args)
        col = gtk.TreeViewColumn("", rend, active = 0)
        tree.append_column(col)

        rend = gtk.CellRendererText()
        col = gtk.TreeViewColumn("", rend, text = 1)
        tree.append_column(col)

        dialog.set_response_sensitive(gtk.RESPONSE_OK, False)


    def create_store(self):
        store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING)
        store.enabled_rows = 0
        for item in self.items:
            store.append((False, item))
        return store


class _SetupListAlert(SetupListAlertTemplate):
    
    _defaults = {
        "list_title": None
    }
    _defaults.update(SetupAlert._defaults)
    
    def get_list_title(self):
        return self.list_title

    def configure_widgets(self, dialog, tree):
        rend = gtk.CellRendererText()
        col = gtk.TreeViewColumn("", rend, text = 0)
        tree.append_column(col)
        tree.get_selection().set_mode(gtk.SELECTION_NONE)


    def create_store(self):
        store = gtk.ListStore(gobject.TYPE_STRING)

        for item in self.items:
            store.append((item,))

        return store
    

class _SetupSingleChoiceList(_SetupListAlert):

    _defaults = {
        "min_select": 1,
    }
    
    _defaults.update(_SetupListAlert._defaults)

    def configure_widgets(self, dialog, tree):
        assert self.min_select in (0, 1)
        
        _SetupListAlert.configure_widgets(self, dialog, tree)
        selection = tree.get_selection()

        if self.min_select == 0:
            selection_mode = gtk.SELECTION_SINGLE
            def on_selection_changed(selection, dialog):
                is_sensitive = selection.count_selected_rows() > 0
                dialog.set_response_sensitive(gtk.RESPONSE_OK, is_sensitive)
            selection.connect("changed", on_selection_changed, dialog)
            
        else:
            selection_mode = gtk.SELECTION_BROWSE

        selection.set_mode(selection_mode)
    


class RunDialog(WidgetCostumizer):
    """
    This is a terminal costumizer because it swaps the gtk.Dialog recieved by
    argument for its `gtk.Dialog.run`'s result.
    """
    def _run(self, dialog, container):
        response = dialog.run()
        dialog.destroy()
        return response, None
        
def hig_alert(primary_text, secondary_text, parent = None, flags = 0, \
              buttons =(gtk.STOCK_OK, gtk.RESPONSE_OK), run = True, \
              _setup_alert = SetupAlert, **kwargs):
              
    if parent is None and "title" not in kwargs:
        raise TypeError("When you don't define a parent you must define a "
                        "title") 
    dlg = gtk.Dialog(parent = parent, flags = flags, buttons = buttons)

    costumizer = SetupDialog()
    
    costumizer.bind(_setup_alert(primary_text, secondary_text, **kwargs))

    if run:
        costumizer.bind(RunDialog())

    return costumizer(dlg)


#################################
# choice_dialog
class _OneStrategy:
    accepts = lambda self, choices, min_select, max_select: choices == 1
    
    def before(self, kwargs):
        pass

    def get_items(self, data):
        return (0,)

class _BaseStrategy:

    def before(self, kwargs):
        kwargs["_setup_alert"] = self.setup_factory


class _MultipleStrategy(_BaseStrategy):
    accepts = lambda self, choices, min_select, max_select: max_select == -1 or\
                                                            max_select > 1
    setup_factory = _SetupMultipleChoiceList

    def get_items(self, dlg):
        # Multiple selection
        store = find_child_widget(dlg, "list_view").get_model()
        return tuple(row.path[0] for row in store if row[0])

class _RadioStrategy(_BaseStrategy):

    accepts = lambda self, choices, min_select, max_select: choices < 5
    setup_factory = _SetupRadioChoiceList
    
    def get_items(self, dlg):
        vbox = find_child_widget(dlg, "items")
        counter = 0
        for radio in vbox.get_children():
            if radio.get_active():
                break
            counter += 1
        assert radio.get_active()
        
        for radio in vbox.get_children():
            vbox.remove(radio)
            radio.destroy()

        return (counter,)

class _SingleListStrategy(_BaseStrategy):
    accepts = lambda self, a, b, c: True
    setup_factory = _SetupSingleChoiceList
    def get_items(self, dlg):
        list_view = find_child_widget(dlg, "list_view")
        rows = list_view.get_selection().get_selected_rows()[1]
        get_element = lambda row: row[0]

        items = tuple(map(get_element, rows))
        
_STRATEGIES = (_OneStrategy, _MultipleStrategy, _RadioStrategy,
               _SingleListStrategy)
_STRATEGIES = tuple(factory() for factory in _STRATEGIES)

def choice(primary_text, secondary_text, parent=None, allow_cancel=True, \
                                                      **kwargs):
    """
    @param items: the items you want to choose from
    @param list_title: the title of the list. Optional.
    @param allow_cancel: If the user can cancel/close the dialog.
    @param min_select: The minimum number of elements to be selected.
    @param max_select: The maximum number of elements to be selected.
        -1 Means no limit.
    
    @param dialog_callback: This is a callback function that is going to be
        called when the dialog is created. The argument is the dialog object.
    @param one_item_text: when specified and if the number of `items` is one
        this text will be the primary text. This string must contain a '%s'
        which will be replaced by the item value.
        Optional.
    """

    if "run" in kwargs:
        del kwargs["run"]
    
    choices = len(kwargs["items"])
    min_select = kwargs.get("min_select", 1)
    max_select = kwargs.get("max_select", -1)

    # Make sure the arguments are correct
    assert choices > 0
    assert (max_select == -1) ^ (min_select <= max_select <= choices)
    assert 0 <= min_select <= choices
    
    buttons = (kwargs.get("ok_button", gtk.STOCK_OK), gtk.RESPONSE_OK)
    
    if allow_cancel:
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL) + buttons
    else:
        # TODO: make closing the window impossible    
        pass

    if min_select == 0:
        txt = N_("Don't select it", "Don't select any items", choices)
        txt = kwargs.get("skip_button", txt)
        buttons = (txt, gtk.RESPONSE_CLOSE) + buttons
    
    for strategy in _STRATEGIES:
        if strategy.accepts(choices, min_select, max_select):
            break
    assert strategy.accepts(choices, min_select, max_select)
    
    if choices == 1:
        if "one_item_text" in kwargs:
            primary_text = kwargs["one_item_text"] % kwargs["items"][0]
    
    data = strategy.before(kwargs)
    if data is not None:
        primary_text = data
    
    dlg = hig_alert(
        primary_text,
        secondary_text,
        parent = parent,
        run = False,
        buttons = buttons,
        **kwargs
    )
    kwargs.get("dialog_callback", lambda foo: None)(dlg)
    response = dlg.run()
    
    if response != gtk.RESPONSE_OK:
        dlg.destroy()
        return (), response
    
    items = strategy.get_items(dlg)
    
    dlg.destroy()
    
    return items, response
    
#############################
# save_changes
_MIN_FRACTION = 60
_HOUR_FRACTION = 60 * _MIN_FRACTION
_DAY_FRACTION = 24 * _HOUR_FRACTION
def _humanize_seconds(elapsed_seconds, use_hours = True, use_days = True):
    """
    Turns a number of seconds into to a human readable string, example
    125 seconds is: '2 minutes and 5 seconds'.
    
    @param elapsed_seconds: number of seconds you want to humanize
    @param use_hours: wether or not to render the hours(if hours > 0)
    @param use_days: wether or not to render the days(if days > 0)
    """
    
    text = []
    
    duration = elapsed_seconds
    
    if duration == 0:
        return _("0 seconds")
    
    days = duration / _DAY_FRACTION
    if use_days and days > 0:
        text.append(N_("%d day", "%d days", days) % days)
        duration %= _DAY_FRACTION
        
    hours = duration / _HOUR_FRACTION
    if use_hours and hours > 0:
        text.append(N_("%d hour", "%d hours", hours) % hours)
        duration %= _HOUR_FRACTION
    
    minutes = duration / _MIN_FRACTION
    if minutes > 0:
        text.append(N_("%d minute", "%d minutes", minutes) % minutes)
        duration %= _MIN_FRACTION

    seconds = duration % 60
    if seconds > 0:
        text.append(N_("%d second", "%d seconds", seconds) % seconds)
    
    if len(text) > 2:
        # To translators: this joins 3 or more time fractions
        return _(", ").join(text[:-1]) + _(" and ") + text[-1]
    else:
        # To translators: this joins 2 or 1 time fractions
        return _(" and ").join(text)

class _TimeUpdater:
    def __init__(self, initial_time):
        self.initial_time = initial_time
    
    def set_dialog(self, dialog):
        self.dialog = dialog
        self.dialog.connect("response", self.on_response)
        self.source = gobject.timeout_add(500, self.on_tick)
    
    def on_response(self, *args):
        gobject.source_remove(self.source)

    def get_text(self):
        last_changes = datetime.datetime.now() - self.initial_time
        # To translators %s is the time
        secondary_text = _("If you don't save, changes from the last %s "
                           "will be permanently lost.")
        return secondary_text % _humanize_seconds(last_changes.seconds)
        
        
    def on_tick(self):
        self.dialog.set_secondary_text(self.get_text())
        return True

def save_changes(files, last_save=None, parent=None, **kwargs):
    """
    Shows up a Save changes dialog to a certain list of documents and returns
    a tuple with two values, the first is a list of files that are to be saved
    the second is the value of the response, which can be one of:
      - gtk.RESPONSE_OK - the user wants to save
      - gtk.RESPONSE_CANCEL - the user canceled the dialog
      - gtk.RESPONSE_CLOSE - the user wants to close without saving
      - gtk.RESPONSE_DELETE_EVENT - the user closed the window
    
    So if you want to check if the user canceled just check if the response is
    equal to gtk.RESPONSE_CANCEL or gtk.RESPONSE_DELETE_EVENT
    
    When the `elapsed_time` argument is not `None` it should be a list of the
    elapsed time since each was modified. It must be in the same order of
    the `files` argument.
    
    This function also accepts every argument that a hig_alert function accepts,
    which means it accepts `title`, etc. Note that this function overrides
    the `run` argument and sets it to True, because it's not possible for a user
    to know which files were saved since the dialog changes is structure
    depending on the arguments.
    
    Simple usage example::
        files_to_save, response = save_changes(["foo.bar"], title="Rat Demo")

    @param files: a list of filenames to be saved
    @param last_save: when you only want to save one file you can optionally
        send the date of when the user saved the file most recently.
        
    @type last_save: datetime.datetime
    @param parent: the window that will be parent of this window.
    @param primary_text: optional, see hig_alert.
    @param secondary_text: optional, see hig_alert.
    @param one_item_text: optional, see choice_alert.
    @param list_title: optional, see choice_alert.
    @param kwargs: the remaining keyword arguments are the same as used on the function
        hig_alert.
    @return: a tuple with a list of entries the user chose to save and a gtk.RESPONSE_*
        from the dialog
    """
    primary_text = N_("There is %d file with unsaved changes. "
                      "Save changes before closing?",
                      "There are %d files with unsaved " 
                      "changes. Save changes before closing?", len(files)) 

    primary_text %= len(files)
    
    primary_text = kwargs.get("primary_text", primary_text)
    
    secondary_text = _("If you don't save, all your changes will be "
                       "permanently lost.")
    
    secondary_text = kwargs.get("secondary_text", secondary_text)

    one_item_text = _("Save the changes to <i>%s</i> before closing?")
    one_item_text = kwargs.get("one_item_text", one_item_text)
    
    list_title = _("Select the files you want to save:")
    list_title = kwargs.get("list_title", list_title)
    
    if len(files) == 1 and last_save is not None:
        updater = _TimeUpdater(last_save)
        secondary_text = updater.get_text()
        kwargs["dialog_callback"] = updater.set_dialog
        
    indexes, response = choice(
        primary_text,
        secondary_text,
        parent = parent,
        min_select = 0,
        max_select = -1,
        skip_button = _("Close without saving"),
        ok_button = gtk.STOCK_SAVE,
        list_title = list_title,
        items = files,
        one_item_text = one_item_text,
        **kwargs
    )

    return map(files.__getitem__, indexes), response

#################
# Common dialogs
def error(primary_text, secondary_text, **kwargs):
    return hig_alert(
        primary_text,
        secondary_text,
        stock = gtk.STOCK_DIALOG_ERROR,
        buttons =(gtk.STOCK_CLOSE, gtk.RESPONSE_OK),
        **kwargs
    )
    

def warning(primary_text, secondary_text, **kwargs):
    return hig_alert(
        primary_text,
        secondary_text,
        stock = gtk.STOCK_DIALOG_WARNING,
        buttons =(gtk.STOCK_CLOSE, gtk.RESPONSE_OK),
        **kwargs
    )

def ok_cancel(primary_text, secondary_text, ok_button=gtk.STOCK_OK, **kwargs):
    return hig_alert(
        primary_text,
        secondary_text,
        stock = gtk.STOCK_DIALOG_WARNING,
        buttons =(
            gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            ok_button, gtk.RESPONSE_OK
        ),
        **kwargs
    )

def info(primary_text, secondary_text, **kwargs):
    return hig_alert(
        primary_text,
        secondary_text,
        stock = gtk.STOCK_DIALOG_INFO,
        buttons =(gtk.STOCK_CLOSE, gtk.RESPONSE_OK),
        **kwargs
    )

def listing(primary_text, secondary_text, parent=None, items=(), **kwargs):
    """
    @param list_title: A label will be placed above the list of items describing
        what's the content of the list. Optional.
    
    Every other argument that L{hig_alert} function does.
    
    Example::
        listing(
            "Listing cool stuff",
            "To select more of that stuff eat alot of cheese!",
            items=["foo", "bar"] * 10, # Some random 20 elements
            title="Rat Demo",
            list_title="Your cool stuff:"
        )
    """
    return hig_alert(
        primary_text,
        secondary_text,
        parent = parent,
        _setup_alert = _SetupListAlert,
        items = items,
        **kwargs
    )


########

class HigProgress(gtk.Window):
    """
    HigProgress returns a window that contains a number of properties to
    access what a common Progress window should have.
    """
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        self.set_border_width(6)
        self.set_resizable(False)
        self.set_title('')
        # defaults to center location
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete-event", self._on_close)
        
        # main container
        main = gtk.VBox(spacing = 12)
        main.set_spacing(12)
        main.set_border_width(6)
        main.show()
        self.add(main)
        
        # primary text
        alg = gtk.Alignment()
        alg.set_padding(0, 6, 0, 0)
        alg.show()
        main.pack_start(alg, False, False)
        lbl = SetupLabel()()
        lbl.set_selectable(False)
        lbl.show()
        self._primary_label = lbl
        alg.add(lbl)
        
        # secondary text
        lbl = SetupLabel()()
        lbl.set_selectable(False)
        lbl.show()
        main.pack_start(lbl, False, False)
        self._secondary_label = lbl
        
        # Progress bar
        vbox = gtk.VBox()
        vbox.show()
        main.pack_start(vbox, False, False)
        
        prog = gtk.ProgressBar()
        prog.show()
        self._progress_bar = prog
        vbox.pack_start(prog, expand = False)
        
        lbl = SetupLabel()()
        lbl.set_selectable(False)
        lbl.show()
        self._sub_progress_label = lbl
        vbox.pack_start(lbl, False, False)
        
        # Buttons box
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.show()
        
        # Cancel Button
        cancel = gtk.Button(gtk.STOCK_CANCEL)
        cancel.set_use_stock(True)
        cancel.show()
        self._cancel = cancel
        bbox.add(cancel)
        main.add(bbox)
        
        # Close button, which is hidden by default
        close = gtk.Button(gtk.STOCK_CLOSE)
        close.set_use_stock(True)
        close.hide()
        bbox.add(close)
        self._close = close
        
    primary_label = property(lambda self: self._primary_label)
    secondary_label = property(lambda self: self._secondary_label)
    progress_bar = property(lambda self: self._progress_bar)
    sub_progress_label = property(lambda self: self._sub_progress_label)
    cancel_button = property(lambda self: self._cancel)
    close_button = property(lambda self: self._close)
    
    def set_primary_text(self, text):
        self.primary_label.set_markup(
            '<span weight="bold" size="larger">'+text+'</span>'
        )
        self.set_title(text)
    
    primary_text = property(fset = set_primary_text)
        
    def set_secondary_text(self, text):
        self.secondary_label.set_markup(text)
    
    secondary_text = property(fset = set_secondary_text)
    
    def set_progress_fraction(self, fraction):
        self.progress_bar.set_fraction(fraction)
    
    def get_progress_fraction(self):
        return self.progress_bar.get_fraction()
        
    progress_fraction = property(get_progress_fraction, set_progress_fraction)
    
    def set_progress_text(self, text):
        self.progress_bar.set_text(text)

    progress_text = property(fset = set_progress_text)
    
    def set_sub_progress_text(self, text):
        self.sub_progress_label.set_markup('<i>'+text+'</i>')
        
    sub_progress_text = property(fset = set_sub_progress_text)
    
    def _on_close(self, *args):
        if not self.cancel_button.get_property("sensitive"):
            return True
        # click on the cancel button
        self.cancel_button.clicked()
        # let the clicked event close the window if it likes too
        return True
        
if __name__ == '__main__':
    items = ["foo", "bar"] * 10
    #items = ["foo", "bar"] * 2
    #items = ["foo"]
    primary_text = "Select an item"
    if len(items) != 1:
        secondary_text = "These items will aid you to do cool stuff"
    else:
        secondary_text = "This item will aid you to do cool stuff"
    list_title = "Items:"
    window_title = "Rat Demo"
    # Simple single selection choice
    #choice(primary_text, secondary_text, items=items, title=window_title, list_title=list_title)
    # Allows the user to not select any element
    #choice_dialog(primary_text, secondary_text, items=items, title=window_title, list_title=list_title, min_select=0)
    # The user must choose at least 2 elements
    listing("This is a nice primary text", "bar", title="Rat", items=("foo", "bar")*20)
#    print choice(
#        primary_text,
#        secondary_text,
#        one_item_text = "Do you want to choose <i>%s</i>?",
#        items=items,
#        title=window_title,
#        list_title=list_title,
#        min_select=0,
#        max_select=1,
#        allow_cancel=False,
#    )

#    print save_changes(["foo"], title="goo", last_save=datetime.datetime.now())

#    dlg = ok_cancel("Rat will simplify your code",
#                            ("By putting common utilities in one place all "
#                             "benefit and get nicer apps."), title="foo", run=False) 


