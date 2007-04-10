
import gtk, gdl

class PidaDock(gdl.Dock):
    """A docking widget"""

DOCK_TERMINAL = 'Terminal'
DOCK_EDITOR = 'Editor'
DOCK_BUFFER = 'Buffer'
DOCK_PLUGIN = 'Plugin'

DOCK_NAMES = [
    DOCK_TERMINAL,
    DOCK_EDITOR,
    DOCK_BUFFER,
    DOCK_PLUGIN,
]

BEH_NORMAL = gdl.DOCK_ITEM_BEH_NORMAL

BEH_ICONONLY = gdl.DOCK_ITEM_BEH_CANT_CLOSE

BEH_PERMANENT = (gdl.DOCK_ITEM_BEH_CANT_CLOSE | gdl.DOCK_ITEM_BEH_CANT_ICONIFY |
                 gdl.DOCK_ITEM_BEH_NEVER_FLOATING | gdl.DOCK_ITEM_BEH_NO_GRIP)

class DockManager(object):

    def __init__(self):
        self._docks = {}
        self._master = gdl.DockMaster()
        for dname in DOCK_NAMES:
            d = self._docks[dname] = PidaDock()
            if dname != DOCK_EDITOR:
                d.unbind()
                d.bind(self._master)

    def get_dock(self, name):
        return self._docks[name]

    def new_dock_item(self, view):
        widget = view.get_toplevel()
        name = str(view.get_unique_id())
        label = view.label_text
        behaviour = view.dock_behaviour
        item = gdl.gdl_dock_item_new(name, label, behaviour)
        item.add(widget)
        view.dock_item = item
        item.props.stock_id = view.icon_name
        tablabel = gtk.HBox()
        icon = view.create_tab_label_icon()
        label = gtk.Label(view.get_tab_label_text())
        tablabel.pack_start(icon, False)
        tablabel.pack_start(label)
        tablabel.show_all()
        item.set_tablabel(tablabel)
        return item

    def add_view(self, dockname, view):
        dock = self.get_dock(dockname)
        item = self.new_dock_item(view)
        dock.add_item(item, gdl.DOCK_CENTER)
        item.show_all()

