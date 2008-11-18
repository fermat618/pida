# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import gtk
import gobject

class DropDownMenuToolButton(gtk.ToggleToolButton):
    __gtype_name__ = "DropDownMenuToolButton"

    # properties
    __gproperties__ = {
        'menu': (gobject.TYPE_OBJECT, 'menu', 'menu that is displayed', gobject.PARAM_READWRITE),
    }
    # signals
    __gsignals__ = {
        'show-menu': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.GObject, ))
    }

    def __init__(self, icon_widget = None, label = None):
        super(DropDownMenuToolButton, self).__init__()
        self._previous_child = None
        self._arrow = None
        self._menu = None
        self._on_menu_deactivate_handler = 0
        if (label is None) and (icon_widget is None):
             self.set_arrow()
        else:
            if (label is not None):
                self.set_label(label)
            if (icon_widget is not None):
                self.set_icon_widget(icon_widget)

        # the button is insentive until we set a menu
        self.get_child().set_sensitive(False)
        self.get_child().connect('toggled', self._on_button__toggled)
        self.get_child().connect('button-press-event', self._on_button__button_press_event)
        self.connect('create-menu-proxy', self._on_create_menu_proxy)

    def set_arrow(self):
        # create arrow
        if (self.get_orientation() == gtk.ORIENTATION_HORIZONTAL):
            self._arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
        else:
            self._arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
        self._arrow.show()
        # show arrow
        if (self.get_child().get_child() is not None):
            self._previous_child = self.get_child().get_child()
            self.get_child().remove(self.get_child().get_child())
        self.get_child().add(self._arrow)
        self.get_child().show()

    def unset_arrow(self):
        if (self._arrow is not None):
            self.get_child().remove(self.get_child().get_child())
            if (self._previous_child is not None):
                self.get_child().add(self._previous_child)
                self._previous_child = None
            self._arrow = None

    def set_label(self, label):
        self.unset_arrow()
        gtk.ToggleToolButton.set_label(self, label)

    def set_label_widget(self, label_widget):
        self.unset_arrow()
        gtk.ToggleToolButton.set_label_widget(self, label_widget)

    def set_icon_name(self, icon_name):
        self.unset_arrow()
        gtk.ToggleToolButton.set_icon_name(self, icon_name)

    def set_icon_widget(self, icon_widget):
        self.unset_arrow()
        gtk.ToggleToolButton.set_icon_widget(self, icon_widget)

    def set_stock_id(self, stock_id):
        print [stock_id]
        return
        self.unset_arrow()
        gtk.ToggleToolButton.set_stock_id(self, stock_id)
    
    def set_menu(self, menu):
        if (menu is not None) and (not isinstance(menu, gtk.Menu)):
            return
        if (self._menu != menu):
            if (self._menu) and (self._menu.get_property('visible')):
                self._menu.deactivate()
            if (self._menu):
                self._menu.handler_disconnect(self._on_menu_deactivate_handler)
                self._menu.detach()

            self._menu = menu

            if (self._menu):
                self._menu.attach_to_widget(self.get_child(), self._menu_detacher)
                self.get_child().set_sensitive(True)
                self._on_menu_deactivate_handler = self._menu.connect('deactivate', self._on_menu__deactivate)
            else:
                self.get_child().set_sensitive(False)

    def get_menu(self):
        return self._menu

    def do_set_property(self, pspec, value):
        if (pspec.name == 'menu'):
            self.set_menu(value)
        else:
            raise AttributeError, 'unknown property %s' % pspec.name

    def do_get_property(self, pspec):
        if (pspec.name == 'menu'):
            return self.get_menu(menu)
        else:
            raise AttributeError, 'unknown property %s' % pspec.name
    
    def do_state_changed(self, state):
        if (not self.get_property('sensitive')) and (self._menu is not None):
            self._menu.deactivate()

    def do_toolbar_reconfigured(self):
        gtk.ToggleToolButton.do_toolbar_reconfigured(self)
        if (self._arrow is not None):
            self.set_arrow()

    def _menu_position_func(self, menu):
        menu_req = menu.size_request()
        orientation = self.get_orientation()
        direction = self.get_direction()
        screen = menu.get_screen()
        monitor_num = screen.get_monitor_at_window(self.get_child().window)
        if (monitor_num < 0):
            monitor_num = 0
        monitor = screen.get_monitor_geometry(monitor_num)

        if (orientation == gtk.ORIENTATION_HORIZONTAL):
            (x, y) = self.get_child().window.get_origin()
            x += self.get_allocation().x
            y += self.get_allocation().y

            if (direction == gtk.TEXT_DIR_LTR):
                x += max(self.get_allocation().width - menu_req[0], 0)
            else:
                if (menu_req[0] > self.get_allocation().width):
                    x -= menu_req[0] - self.get_allocation().width

            if ((y + self.get_child().get_allocation().height + menu_req[1]) <= monitor.y + monitor.height):
                y += self.get_child().get_allocation().height
            else:
                if ((y - menu_req[1]) >= monitor.y):
                    y -= menu_req[1]
                else:
                    if ((monitor.y + monitor.height - (y + self.get_child().get_allocation().height)) > y):
                        y += self.get_child().get_allocation().height
                    else:
                        y -= menu_req[1]
        else:
            (x, y) = self.get_child().window.get_origin()# actually event_window
            req = self.get_child().size_request()
            if (direction == gtk.TEXT_DIR_LRT):
                x += self.get_child().get_allocation().width
            else:
                x -= menu_req.width
            if ((y + menu_req.height) > (monitor.y + monitor.height)) and ((y + self.get_child().get_allocation().height - monitor.y) > (monitor.y + monitor.height -y )):
                y += self.get_child().get_allocation().height - menu_req.height
        
        return (x, y, False)

    
    def _popup_menu_under_arrow(self, event):
        self.emit('show-menu', self)
        if (self._menu is None):
            return
        button = 0
        time = gtk.get_current_event_time()
        if (event is not None):
            button = event.button
            time = event.time
        self._menu.popup(None, None, self._menu_position_func, button, time)
    
    def _on_button__toggled(self, button):
        if (self._menu is None):
            return
        if (self.get_child().get_active()) and (not self._menu.get_property('visible')):
            # we get here only when the menu is activated by a key
            # press, so that we can select the first menu item
            self._popup_menu_under_arrow(None)
            self._menu.select_first(False)

    def _on_create_menu_proxy(self, toolitem):
        # create the overflow menu
        m = gtk.MenuItem(' ')
        menu = gtk.Menu()
        for c in self.get_menu().get_children():
            action = c.get_action()
            if action is not None:
                mi = action.create_menu_item()
            else:
                mi = gtk.SeparatorMenuItem()
            menu.append(mi)
        m.set_submenu(menu)
        m.show_all()
        self.set_proxy_menu_item("gtk-tool-button-menu-id", m)
        return True
        
    def _on_button__button_press_event(self, button, event):
        if (event.button == 1):
            self._popup_menu_under_arrow(event);
            self.get_child().set_active(True)
            return True
        else:
            return False
    
    def _on_menu__deactivate(self, menu):
        self.get_child().set_active(False)

    def _menu_detacher(self, widget, menu):
        if (self._menu != menu):
            return
        self._menu = None


gobject.type_register(DropDownMenuToolButton)

def test():
    window = gtk.Window()
    window.resize(200,100)
    window.connect('destroy', gtk.main_quit)
    
    toolbar = gtk.Toolbar()
    window.add(toolbar)

    menu = gtk.Menu()
    menu.append(gtk.MenuItem('menuitem 1'))
    menu.append(gtk.MenuItem('menuitem 2'))
    menu.append(gtk.MenuItem('menuitem 3'))
    menu.append(gtk.MenuItem('menuitem 4'))
    menu.append(gtk.MenuItem('menuitem 5'))
    menu.show_all()

    action = gtk.Action('menu', None, 'Tooltip', None)
    action.set_tool_item_type(DropDownMenuToolButton)
    toolitem = action.create_tool_item()
    print "set arrow"
    toolitem.set_arrow()
    print "set label"
    toolitem.set_label("test")
    print "set arrow"
    toolitem.set_arrow()
    print "set stock id"
    toolitem.set_label(None)
    toolitem.set_stock_id(gtk.STOCK_SELECT_ALL)
    print "set arrow"
    toolitem.set_arrow()
    print "set icon widget"
    arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
    arrow.show()
    toolitem.set_icon_widget(arrow)
    print "set arrow"
    toolitem.set_arrow()
    #
    toolitem.set_property('menu', menu)
    toolbar.insert(toolitem, 0)
    
    window.show_all()    
    gtk.main()


if (__name__ == '__main__'):
    test()


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
