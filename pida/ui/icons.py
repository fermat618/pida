# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os
import gtk


class IconRegister(object):

    def __init__(self):
        self._factory = gtk.IconFactory()
        self._factory.add_default()
        self._register_theme_icons()

    def register_file_icons_for_directory(self, directory):
        for filename in os.listdir(directory):
            name, ext = os.path.splitext(filename)
            if ext in ['.png', '.gif', '.svg', '.jpg']:
                path = os.path.join(directory, filename)
                self._stock_add(name)
                self._register_file_icon(name, path)

    def _register_theme_icons(self):
        stock_ids = gtk.stock_list_ids()
        for name in gtk.icon_theme_get_default().list_icons():
            if name not in stock_ids:
                self._stock_add(name)
                self._register_theme_icon(name)

    def _stock_add(self, name, label=None):
        if label is None:
            label = name.capitalize()
        gtk.stock_add([(name, label, 0, 0, None)])

    def _register_theme_icon(self, name):
        icon_set = gtk.IconSet()
        self._register_icon_set(icon_set, name)

    def _register_file_icon(self, name, filename):
        #im = gtk.Image()
        #im.set_from_file(filename)
        #pb = im.get_pixbuf()
        try:
            pb = gtk.gdk.pixbuf_new_from_file_at_size(filename, 32, 32)
            icon_set = gtk.IconSet(pb)
            self._register_icon_set(icon_set, name)
        except:
            #XXX: there is a image loader missing
            #     for *.svg its librsvg + its gtk pixmap loader
            print filename
        # this is broken for some reason
        #gtk.icon_theme_add_builtin_icon(name, gtk.ICON_SIZE_SMALL_TOOLBAR, pb)

    def _register_icon_set(self, icon_set, name):
        source = gtk.IconSource()
        source.set_icon_name(name)
        icon_set.add_source(source)
        self._factory.add(name, icon_set)






#w = gtk.Window()
#i = gtk.Image()
#i.set_from_stock("foo", gtk.ICON_SIZE_DIALOG)
#w.add(i)
#w.show_all()
#w.connect('destroy', gtk.main_quit)
#gtk.main()
