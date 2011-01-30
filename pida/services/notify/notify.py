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
import gtk
import datetime
import locale
import logbook

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
from pygtkhelpers.gthreads import gcall

# locale
from pida.core.locale import Locale
_locale = Locale('notify')
_ = _locale.gettext

import pynotify
pynotify.init('PIDA')

from logbook.handlers import Handler, StreamHandler
from pida.core.log import rollover

class MainloopSendHandler(Handler):
    def __init__(self, handlers):
        Handler.__init__(self)
        self.handlers = handlers

    def _in_mainloop(self, record):
        for handler in self.handlers:
            handler.emit(record)

    def close(self):
        for handler in self:
            handler.close()

    def emit(self, record):
        gcall(self._in_mainloop, record)


class TextBufferStream(object):
    def __init__(self, max_length=50000):
        self.max_length = max_length
        self.buffer = gtk.TextBuffer()

    def write(self, data):
        self.buffer.insert(self.buffer.get_end_iter(), data)
        drang = self.buffer.get_char_count() - self.max_length
        if drang > 0:
            titer = self.buffer.get_end_iter(drang)
            titer.forward_to_line_end()
            self.buffer.delete(self.buffer.get_start_iter(), titer)

class ErrorCallerHandler(Handler):
    def __init__(self, callback):
        Handler.__init__(self, level=logbook.ERROR)
        self.callback = callback

    def emit(self, record):
        if record.level>=self.level:
            self.callback(self, record)



class NotifyItem(object):

    def __init__(self, data, title, stock, timeout, callback):
        self.data = cgi.escape(str(data) or "")
        self.title = cgi.escape(str(title) or "")
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

    def __init__(self, svc, buffer):
        self.buffer = buffer
        PidaView.__init__(self, svc)

    def create_ui(self):
        self._hbox = gtk.HBox(spacing=3)
        self._hbox.set_border_width(6)
        self.text_view = gtk.TextView(self.buffer)
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


class NotifyOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_notify',
            _('Show notifications'),
            bool,
            True,
            _('Show notifications popup'),
        )


        self.create_option(
            'timeout',
            _('Timeout'),
            int,
            6000,
            _('Timeout before hiding a notification'),
        )


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
        self._error_handler =  ErrorCallerHandler(self._on_error)
        self._log_stream = TextBufferStream()
        self._log_handler = MainloopSendHandler([
            self._error_handler,
            logbook.StreamHandler(self._log_stream),
        ])
        rollover.rollover(self._log_handler)
        self._view = NotifyView(self)
        self._log = LogView(self, self._log_stream.buffer)

        self._has_loaded = False

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
        if self.opt('show_notify'):
            n = pynotify.Notification(item.title, item.data, item.stock)
            n.set_timeout(item.timeout)
            try:
                n.show()
            except:
                # depending on the notifier daemon, sometimes a glib.GError is raised
                # here.
                pass

    def _on_error(self, handler, record):
        self.notify(record.message, timeout=20000,
                    title=_("Pida error occured in %s") %record.channel)


    def notify(self, data, title='', stock=gtk.STOCK_DIALOG_INFO,
            timeout=None, callback=None, quick=False):
        if timeout is None:
            timeout = 700 if quick else self.opt('timeout')
        self.add_notify(NotifyItem(data=data, title=title, stock=stock,
            timeout=timeout, callback=callback))

    def stop(self):
        if self.get_action('show_notify').get_active():
            self.hide_notify()



Service = Notify

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
