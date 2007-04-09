import gtk
 
def register_named_icon(stock_id, icon_name, factory):
    source = gtk.IconSource()
    source.set_icon_name(icon_name)
    icon_set = gtk.IconSet()
    icon_set.add_source(source)
    factory.add(stock_id, icon_set)
 
# like gtk.stock_add but every tuple element contains also icon name
def my_stock_add(items):
    factory = gtk.IconFactory()
    factory.add_default()
    gtk.stock_add([it[:-1] for it in items])
    for it in items:
        register_named_icon(it[0], it[-1], factory)
        # and this:
        # gtk.icon_theme_add_builtin_icon(icon_name, size, pixbuf)
 
my_stock_add([("terminal", "Terminal", 0, 0, None, "terminal")])
 
#w = gtk.Window()
#i = gtk.Image()
#i.set_from_stock("foo", gtk.ICON_SIZE_DIALOG)
#w.add(i)
#w.show_all()
#w.connect('destroy', gtk.main_quit)
#gtk.main()
