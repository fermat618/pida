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

from urlparse import urljoin

import gtk, webkit

from pygtkhelpers.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.ui.views import PidaGladeView, WindowConfig
from pida.ui.htmltextview import HtmlTextView

from pida.utils.web import fetch_url
from pida.utils.feedparser import parse

# locale
from pida.core.locale import Locale
locale = Locale('trac')
_ = locale.gettext

class TracView(PidaGladeView):

    key = 'trac.browser'

    gladefile = 'trac_browser'
    locale = locale
    icon_name = 'trac_logo'
    label_text = _('Trac')

    def create_ui(self):
        self.tickets_list.set_columns([
            Column('ticket', sorted=True, type=int),
            Column('summary'),
        ])
        self.set_base_address('http://pida.co.uk/trac/')
        self.item_text = webkit.WebView()
        self.item_text_holder.add(self.item_text)
        self.item_text.show()

    def set_base_address(self, address):
        self._address = address
        self.address_entry.set_text(address)

    def get_base_address(self):
        return self.address_entry.get_text()

    def get_auth_data(self):
        if self.toggle_auth.get_active():
            return (self.user_entry.get_text(), self.password_entry.get_text())

    def on_connect_button__clicked(self, button):
        trac_report(self.get_base_address(), 1, self.report_received,
                    self.get_auth_data())

    def on_tickets_list__selection_changed(self, ol):
        item = ol.selected_item
        self.item_text.load_html_string(item.description.strip(), self._address)

    def on_toggle_auth__toggled(self, btn):
        self.auth_box.set_sensitive(btn.get_active())

    def report_received(self, url, data):
        self.tickets_list.clear()
        if url:
            # no error
            for item in parse_report(data):
                self.tickets_list.append(item)
        else:
            # an error occured
            self.svc.boss.cmd('notify', 'notify', title=data,
                data=_('An error occured when fetching trac tickets.'))


    def can_be_closed(self):
        self.svc.get_action('show_trac').set_active(False)


class ReportItem(object):
    def __init__(self, entry):
        ticket, summary = entry['title'].split(':', 1)
        self.ticket = int(ticket.strip('#').strip())
        self.summary = summary.strip()
        self.description = entry['description']


def parse_report(data):
    feed = parse(data)
    for entry in feed.entries:
        yield ReportItem(entry)

def trac_report(base_address, report_id, callback, auth):
    action_fragment = 'report/%s?format=rss' % report_id
    action_url = urljoin(base_address, action_fragment)
    fetch_url(action_url, callback, auth=auth)

class TracActions(ActionsConfig):

    def create_actions(self):
        TracWindowConfig.action = self.create_action(
            'show_trac',
            TYPE_REMEMBER_TOGGLE,
            _('Trac Viewer'),
            _('Show the Trac Viewer'),
            gtk.STOCK_INFO,
            self.on_show_trac,
            '<Shift><Control>j',
        )


    def on_show_trac(self, action):
        if action.get_active():
            self.svc.show_trac()
        else:
            self.svc.hide_trac()

class TracWindowConfig(WindowConfig):
    key = TracView.key
    label_text = TracView.label_text

class TracFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            TracWindowConfig)

# Service class
class Trac(Service):
    """Describe your Service Here"""

    actions_config = TracActions
    features_config = TracFeaturesConfig

    def pre_start(self):
        self._view = TracView(self)

    def show_trac(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_trac(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def ensure_view_visible(self):
        action = self.get_action('show_trac')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'presnet_view', view=self._view)

    def stop(self):
        if self.get_action('show_trac').get_active():
            self.hide_trac()


# Required Service attribute for service loading
Service = Trac



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
