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

import cgi
import gtk, gobject
import datetime
import locale

from kiwi.ui.objectlist import Column, ObjectList
from pida.core.environment import get_uidef_path
from pida.ui.views import PidaView
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.options import OptionsConfig, choices
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, TYPE_TOGGLE
from pida.ui.buttons import create_mini_button

# locale
from pida.core.locale import Locale
_locale = Locale('notify')
_ = _locale.gettext


class NotifyItem(object):

    def __init__(self, data, title, stock, timeout, callback):
        self.data = cgi.escape(data)
        self.title = cgi.escape(title)
        self.stock = stock
        self.timeout = timeout
        self.time = datetime.datetime.today().strftime(
                locale.nl_langinfo(locale.D_T_FMT))
        self.callback = callback

    @property
    def markup(self):
        if self.title != '':
            return '<b>%s</b>\n%s' % (self.title, self.data)
        return self.data

    def cb_clicked(self, w, ev):
        if self.callback is not None:
            self.callback(self)


class NotifyView(PidaView):

    label_text = _('Notifications')
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self._hbox = gtk.HBox(spacing=3)
        self._hbox.set_border_width(6)
        self.create_list()
        self.create_toolbar()
        self.add_main_widget(self._hbox)
        self._hbox.show_all()

    def create_list(self):
        self.notify_list = ObjectList([
                Column('stock', use_stock=True),
                Column('time', sorted=True, order=gtk.SORT_DESCENDING),
                Column('markup', use_markup=True, expand=True),
            ])
        self.notify_list.set_headers_visible(False)
        self.notify_list.connect('double-click', self.on_notify_list_click)
        self._hbox.pack_start(self.notify_list)

    def create_toolbar(self):
        self._bar = gtk.VBox(spacing=1)
        self._clear_button = create_mini_button(
            gtk.STOCK_DELETE, _('Clear history'),
            self.on_clear_button)
        self._bar.pack_start(self._clear_button, expand=False)
        self._hbox.pack_start(self._bar, expand=False)
        self._bar.show_all()

    def on_notify_list_click(self, olist, item):
        item.cb_clicked(None, None)

    def on_clear_button(self, w):
        self.clear()

    def add_item(self, item):
        self.notify_list.append(item)

    def can_be_closed(self):
        self.svc.get_action('show_notify').set_active(False)

    def clear(self):
        self.notify_list.clear()

class NotifyPopupView(object):

    def __init__(self, svc):
        self.svc = svc
        self.win = gtk.Window(gtk.WINDOW_POPUP)
        self.win.set_border_width(3)
        self.win.set_resizable(False)
        self.win.set_name('gtk-tooltips')
        self.win.connect_after('expose_event', self.expose)
        self.win.connect('size-request', self.on_size_request)
        self.win.set_events(gtk.gdk.POINTER_MOTION_MASK)
        self.win.set_transient_for(self.svc.window)
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        self.counter = 0

    def set_gravity(self, gravity):
        if gravity == _('North East'):
            self.win.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        if gravity == _('North West'):
            self.win.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        if gravity == _('South East'):
            self.win.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)
        if gravity == _('South West'):
            self.win.set_gravity(gtk.gdk.GRAVITY_SOUTH_WEST)

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

    def on_size_request(self, widget, requisition):
        width, height = self.win.get_size()
        gravity = self.win.get_gravity()
        x = 0
        y = 0
        if gravity == gtk.gdk.GRAVITY_NORTH_EAST or gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                    x = gtk.gdk.screen_width() - width
        if gravity == gtk.gdk.GRAVITY_SOUTH_WEST or gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                    y = gtk.gdk.screen_height() - height
        self.win.move(x, y)

    def add_item(self, item):

        # create layout
        eventbox = gtk.EventBox()
        eventbox.set_events(eventbox.get_events() | gtk.gdk.BUTTON_PRESS_MASK)
        eventbox.connect('button-press-event', item.cb_clicked)
        hbox = gtk.HBox()

        # create stock
        image = gtk.image_new_from_stock(item.stock, gtk.ICON_SIZE_MENU)
        image.set_padding(4, 5)
        hbox.pack_start(image, expand=False)

        # create markup
        label = gtk.Label()
        label.set_alignment(0, 0.5)
        label.set_padding(10, 5)
        label.set_markup(item.markup)
        hbox.pack_start(label)

        # add item in vbox, and show popup
        eventbox.add(hbox)
        self.vbox.pack_start(eventbox)
        self.win.show_all()

        # don't remenber to hide him later
        self.counter += 1
        gobject.timeout_add(item.timeout, self._remove_item, eventbox)

    def _remove_item(self, widget):
        self.vbox.remove(widget)
        self.counter -= 1

        # hide window if we don't have elements
        if self.counter == 0:
            self.win.hide()

class NotifyOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_notify',
            _('Show notifications'),
            bool,
            True,
            _('Show notifications popup'),
            self.on_show_notify
        )

        self.create_option(
            'timeout',
            _('Timeout'),
            int,
            6000,
            _('Timeout before hiding a notification'),
            self.on_change_timeout
        )

        self.create_option(
            'gravity',
            _('Gravity'),
            choices([
                _('North East'),
                _('North West'),
                _('South East'),
                _('South West'),
                ]),
            _('South East'),
            _('Position of notifications popup'),
            self.on_gravity_change
           )

    def on_show_notify(self, client, id, entry, option):
        self.svc._show_notify = option.get_value()

    def on_change_timeout(self, client, id, entry, option):
        self.svc._timeout = option.get_value()

    def on_gravity_change(self, client, id, entry, option):
        self.svc._popup.set_gravity(option.get_value())


class NotifyActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_notify',
            TYPE_TOGGLE,
            _('Show notification history'),
            _('Show the notifications history'),
            '',
            self.on_show_notify,
            '',
        )


    def on_show_notify(self, action):
        if action.get_active():
            self.svc.show_notify()
        else:
            self.svc.hide_notify()

class NotifyCommandsConfig(CommandsConfig):
    def notify(self, data, **kw):
        self.svc.notify(data=data, **kw)


class Notify(Service):
    """
    Notify user from something append
    """

    actions_config = NotifyActionsConfig
    commands_config = NotifyCommandsConfig
    options_config = NotifyOptionsConfig

    def start(self):
        self._view = NotifyView(self)
        self._popup = NotifyPopupView(self)
        self._has_loaded = False
        self._show_notify = self.opt('show_notify')
        self._timeout = self.opt('timeout')
        self._popup.set_gravity(self.opt('gravity'))

    def show_notify(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_notify(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def add_notify(self, item):
        self._view.add_item(item)
        if self._show_notify:
            self._popup.add_item(item)

    def notify(self, data, title='', stock=gtk.STOCK_DIALOG_INFO,
            timeout=-1, callback=None):
        if timeout == -1:
            timeout = self._timeout
        self.add_notify(NotifyItem(data=data, title=title, stock=stock,
            timeout=timeout, callback=callback))

    def stop(self):
        if self.get_action('show_notify').get_active():
            self.hide_notify()


Service = Notify

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
