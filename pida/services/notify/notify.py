# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

#
# Some part of code are taken of old Gajim version : 
# http://trac.gajim.org/browser/trunk/src/tooltips.py
#

import cgi
import gtk, gobject
import datetime
import locale
import logging

from pygtkhelpers.utils import gsignal
from pygtkhelpers.ui.objectlist import Column, ObjectList
from pida.ui.views import PidaView, WindowConfig
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.options import OptionsConfig, choices
from pida.core.actions import (ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, 
                               TYPE_REMEMBER_TOGGLE)
from pida.ui.buttons import create_mini_button
from pida.utils.gthreads import gcall
import gobject

# locale
from pida.core.locale import Locale
_locale = Locale('notify')
_ = _locale.gettext

import StringIO

class PidaLogHandler(gobject.GObject, logging.Handler):
    """
    The PidaLogHandler saved all log entries to be displayed in a log window,
    and let the notify service popup a notify on errors
    """

    gsignal('errors', object)

    def __init__(self, *args, **kwargs):
        self.error_stack = []
        self.max_length = kwargs.get('max_length', 50000)
        self.buffer = gtk.TextBuffer()
        gobject.GObject.__init__(self)
        logging.Handler.__init__(self, *args, **kwargs)
    
    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to encode the message before
        output to the stream.
        """
        try:
            if record.levelno >= logging.ERROR and \
               isinstance(self.error_stack, list):
                self.error_stack.append(record)
                gobject.GObject.emit(self, 'errors', record)

            msg = self.format(record)
            #stream = self.stream
            fs = "%s\n"
            try:
                if (isinstance(msg, unicode)):
                    self.buffer.insert(self.buffer.get_end_iter(),
                                       fs % msg)
                else:
                    self.buffer.insert(self.buffer.get_end_iter(),
                                       fs % msg.encode('UTF-8'))

            except UnicodeError:
                self.buffer.insert(self.buffer.get_end_iter(),
                                        fs % msg.encode('UTF-8'))
        except:
            self.handleError(record)

        # cleanup size
        drang = self.buffer.get_char_count() - self.max_length
        if drang > 0:
            self.buffer.delete(self.buffer.get_start_iter(),
                               self.buffer.get_iter_at_offset(drang))

gobject.type_register(PidaLogHandler)

PIDAHANDLER = PidaLogHandler()
PIDAHANDLER.setFormatter(
logging.Formatter("%(asctime)s - %(levelname)s -  %(name)s - %(message)s"))

logging.getLogger('').addHandler(PIDAHANDLER)


class BaseNotifier(object):

    def __init__(self, svc):
        self.svc = svc

    def notify(self, item):
        raise NotImplementedError


class NIHNotifier(BaseNotifier):

    def __init__(self, svc):
        BaseNotifier.__init__(self, svc)
        self._popup = NotifyPopupView(self.svc)
        self._popup.on_pida_window = self.svc.opt('pidawindow')
        self._popup.set_gravity(self.svc.opt('gravity'))

    def notify(self, item):
        self._popup.add_item(item)


class LibNotifyNotifier(BaseNotifier):

    def notify(self, item):
        n = pynotify.Notification(item.title, item.data, item.stock)
        n.set_timeout(item.timeout)
        try:
            n.show()
        except:
            # depending on the notifier daemon, sometimes a glib.GError is raised
            # here.
            pass

try:
    import pynotify
    pynotify.init('PIDA')
    Notifier = LibNotifyNotifier
except ImportError:
    pynotify = None
    Notifier = NIHNotifier



class NotifyItem(object):

    def __init__(self, data, title, stock, timeout, callback):
        self.data = cgi.escape(data or "")
        self.title = cgi.escape(title or "")
        self.stock = stock
        self.timeout = timeout
        try:
            self.time = datetime.datetime.today().strftime(
                locale.nl_langinfo(locale.D_T_FMT))
        except: # here locale is broken
            self.time = "<unknown>"
        self.callback = callback

    @property
    def markup(self):
        if self.title != '':
            return '<b>%s</b>\n%s' % (self.title, self.data)
        return self.data

    def cb_clicked(self, w, ev):
        if self.callback is not None:
            self.callback(self)

class LogView(PidaView):

    key = "notify.debug"

    label_text = _('Pida Log')
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self._hbox = gtk.HBox(spacing=3)
        self._hbox.set_border_width(6)
        self.text_view = gtk.TextView(PIDAHANDLER.buffer)
        self._scroll = gtk.ScrolledWindow()
        self._scroll.add(self.text_view)
        self._hbox.add(self._scroll)
        self.add_main_widget(self._hbox)
        self._hbox.show_all()

    def can_be_closed(self):
        self.svc.get_action('show_pida_log').set_active(False)


class NotifyView(PidaView):

    key = "notify.view"

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
                Column('time', sorted=True),
                Column('markup', use_markup=True, expand=True),
            ])
        self.notify_list.set_headers_visible(False)
        self._hbox.pack_start(self.notify_list)

    def create_toolbar(self):
        self._bar = gtk.VBox(spacing=1)
        self._clear_button = create_mini_button(
            gtk.STOCK_DELETE, _('Clear history'),
            self.on_clear_button)
        self._bar.pack_start(self._clear_button, expand=False)
        self._hbox.pack_start(self._bar, expand=False)
        self._bar.show_all()

    def on_notify_list__item_activated(self, olist, item):
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
        self.on_pida_window = False
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

        if self.on_pida_window:
            twin = self.svc.boss.window.window
            x, y = twin.get_position()
            if gravity == gtk.gdk.GRAVITY_NORTH_EAST or gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                        x = twin.get_position()[0] + twin.get_size()[0] - width
            if gravity == gtk.gdk.GRAVITY_SOUTH_WEST or gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                        y = twin.get_position()[1] + twin.get_size()[1] - height

        else:
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

        if pynotify is not None:
            return

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

        self.create_option(
            'pidawindow',
            _('On pida window'),
            bool,
            False,
            _('Attach notifications on pida window'),
            self.on_pida_window_change
        )


    def on_show_notify(self, option):
        self.svc._show_notify = option.value

    def on_change_timeout(self, option):
        self.svc._timeout = option.value

    def on_gravity_change(self, option):
        self.svc.notifier._popup.set_gravity(option.value)

    def on_pida_window_change(self, option):
        self.svc.notifier._popup.on_pida_window = option.value


class NotifyActionsConfig(ActionsConfig):

    def create_actions(self):
        NotifyWindowConfig.action = self.create_action(
            'show_notify',
            TYPE_REMEMBER_TOGGLE,
            _('Show notification _history'),
            _('Show the notifications history'),
            '',
            self.on_show_notify,
            '',
        )
        self.create_action(
            'show_pida_log',
            TYPE_REMEMBER_TOGGLE,
            _('Show Pida Log'),
            _('Show the log file pida generates'),
            '',
            self.on_show_pida_log,
            '',
        )


    def on_show_pida_log(self, action):
        if action.get_active():
            self.svc.show_pida_log()
        else:
            self.svc.hide_pida_log()

    def on_show_notify(self, action):
        if action.get_active():
            self.svc.show_notify()
        else:
            self.svc.hide_notify()

class NotifyCommandsConfig(CommandsConfig):
    def notify(self, data, **kw):
        self.svc.notify(data=data, **kw)

class NotifyWindowConfig(WindowConfig):
    key = NotifyView.key
    label_text = NotifyView.label_text
    description = _("Window with notifications")

class NotifyFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            NotifyWindowConfig)


class Notify(Service):
    """
    Notify user from something append
    """

    actions_config = NotifyActionsConfig
    commands_config = NotifyCommandsConfig
    options_config = NotifyOptionsConfig
    features_config = NotifyFeaturesConfig
    
    def start(self):
        self._error_handler = PIDAHANDLER.connect('errors', self._on_error)

        self._view = NotifyView(self)
        self._log = LogView(self)

        self.notifier = Notifier(self)

        self._has_loaded = False
        self._show_notify = self.opt('show_notify')

        # send already occured errors
        #while True:
        #    try:
        #        error = PIDAHANDLER.error_stack.pop()
        #    except IndexError:
        #        break
        #    self._on_error(None, error)
        #PIDAHANDLER.error_stack = None

    def show_notify(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_notify(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def show_pida_log(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._log)

    def hide_pida_log(self):
        self.boss.cmd('window', 'remove_view', view=self._log)


    def add_notify(self, item):
        if not self.started:
            gcall(self.add_notify, item)
            return
        self._view.add_item(item)
        if self._show_notify:
            self.notifier.notify(item)

    def _on_error(self, handler, msg):
        self.notify(msg.getMessage(), timeout=20000,
                    title=_("Pida error occured in %s") %msg.name)


    def notify(self, data, title='', stock=gtk.STOCK_DIALOG_INFO,
            timeout=-1, callback=None, quick=False):
        if timeout == -1:
            if quick:
                timeout = 700
            else:
                timeout = self.opt('timeout')
        self.add_notify(NotifyItem(data=data, title=title, stock=stock,
            timeout=timeout, callback=callback))

    def stop(self):
        if self.get_action('show_notify').get_active():
            self.hide_notify()
        PIDAHANDLER.disconnect(self._error_handler)



Service = Notify

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
