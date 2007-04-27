import gtk

def create_mini_button(stock_id, tooltip, click_callback):
    tip = gtk.Tooltips()
    tip.enable()
    im = gtk.Image()
    im.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
    but = gtk.Button()
    but.set_image(im)
    but.connect('clicked', click_callback)
    eb = gtk.EventBox()
    eb.add(but)
    tip.set_tip(eb, tooltip)
    return eb

