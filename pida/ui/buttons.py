# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

def create_mini_button(stock_id, tooltip, click_callback, toggleButton=False):
    tip = gtk.Tooltips()
    tip.enable()
    im = gtk.Image()
    im.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
    if toggleButton:
        but = gtk.ToggleButton()
        if click_callback:
            but.connect('toggled', click_callback)
    else:
        but = gtk.Button()
        if click_callback:
            but.connect('clicked', click_callback)
    but.set_image(im)
    eb = gtk.EventBox()
    eb.add(but)
    tip.set_tip(eb, tooltip)
    return eb

