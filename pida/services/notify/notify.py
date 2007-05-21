# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

#
# Some part of code are taken of old Gajim version : 
# http://trac.gajim.org/browser/trunk/src/tooltips.py
#


import os, re, sre_constants, cgi
import gtk, gobject

from glob import fnmatch

from kiwi.ui.objectlist import Column, ObjectList
from pida.ui.views import PidaGladeView, PidaView
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, OTypeInteger
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask, gcall
from pida.utils.testing import refresh_gui

# locale
from pida.core.locale import Locale
locale = Locale('notify')
_ = locale.gettext


class NotifyItem(object):

    def __init__(self, data, title, icon):
        self.data = data
        self.title = title
        self.icon = icon


class NotifyView(PidaView):

    def create_ui(self):
        self.__vbox = gtk.VBox(spacing=3)
        self.__vbox.set_border_width(6)
        self.notify_list = ObjectList([
                Column('data', title=_('Notification'), expand=True),
            ])
        self.__vbox.pack_start(self.notify_list)
        self.add_main_widget(self.__vbox)
        self.__vbox.show_all()

    def add_item(self, item):
        self.notify_list.append(item)

class NotifyPopupView(object):

    def __init__(self):
        self.win = gtk.Window(gtk.WINDOW_POPUP)
        self.win.set_border_width(3)
        self.win.set_resizable(False)
        self.win.set_name('gtk-tooltips')
        self.win.connect_after('expose_event', self.expose)
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        self.counter = 0

    def expose(self, widget, event):
        style = self.win.get_style()
        size = self.win.get_size()
        style.paint_flat_box(self.win.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                None, self.win, 'tooltip', 0, 0, -1, 1)
        style.paint_flat_box(self.win.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                None, self.win, 'tooltip', 0, size[1] - 1, -1, 1)
        style.paint_flat_box(self.win.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                None, self.win, 'tooltip', 0, 0, 1, -1)
        style.paint_flat_box(self.win.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                None, self.win, 'tooltip', size[0] - 1, 0, 1, -1)
        return True

    def populate(self, data, title=None, icon=None):

        hbox = gtk.HBox()

        # create icon
        if icon is not None:
            image = gtk.image_new_from_stock(icon, gtk.ICON_SIZE_MENU)
        else:
            image = gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_MENU)
        hbox.pack_start(image)

        # create markup
        if title is not None:
            markup = '<b>%s</b>\n%s' % (title, data)
        else:
            markup = data
        label = gtk.Label()
        label.set_padding(4, 5)
        label.set_markup(markup)
        hbox.pack_start(label)

        self.vbox.pack_start(hbox)
        self.win.show_all()
        gobject.timeout_add(2000, self._remove_notify, hbox)

    def add_item(self, item):
        self.counter += 1
        self.populate(item.data, item.title, item.icon)

    def _remove_notify(self, label):
        self.vbox.remove(label)
        self.counter -= 1
        if self.counter == 0:
            self.win.hide()

class NotifyActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_notify',
            TYPE_TOGGLE,
            _('Notifications'),
            _('Show the notifications'),
            '',
            self.on_show_notify,
            '',
        )

    def on_show_notify(self, action):
        if action.get_active():
            self.svc.show_notify()
        else:
            self.svc.hide_notify()


class Notify(Service):
    """
    Notify user from something append
    """

    actions_config = NotifyActions

    def start(self):
        self._view = NotifyView(self)
        self._popup = NotifyPopupView()
        self._has_loaded = False

    def show_notify(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_notify(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def add_notify(self, item):
        self._popup.add_item(item)
        self._view.add_item(item)

    def notify(self, data, title=None, icon='default'):
        self.add_notify(NotifyItem(data=data, title=title, icon=icon))

    def stop(self):
        if self.get_action('show_notify').get_active():
            self.hide_notify()


Service = Notify

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
