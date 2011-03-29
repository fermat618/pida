import gtk

from pida.ui.dropdownmenutoolbutton import DropDownMenuToolButton


class PidaMenuToolAction(gtk.Action):
    """
    Custom gtk.Action subclass for handling toolitems with a dropdown menu
    attached.
    """

    __gtype_name__ = "PidaMenuToolAction"

    def __init__(self, *args, **kw):
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(gtk.MenuToolButton)


class PidaDropDownMenuToolAction(gtk.Action):
    """
    Custom gtk.Action subclass for handling toolitems with a dropdown menu
    attached.
    """

    __gtype_name__ = "PidaDropDownMenuToolAction"

    def __init__(self, *args, **kw):
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(DropDownMenuToolButton)
        self._set_arrow = not kw['label'] and not kw['stock_id']

    def create_tool_item(self):
        toolitem = gtk.Action.create_tool_item(self)
        if self._set_arrow:
            toolitem.set_arrow()
        return toolitem


class PidaRememberToggle(gtk.ToggleAction):
    """Remembers the state of the toggle on restart"""

    __gtype_name__ = "PidaRememberToggle"

    def __init__(self, *args, **kw):
        gtk.ToggleAction.__init__(self, *args, **kw)
