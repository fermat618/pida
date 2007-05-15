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

import gtk
import xmlrpclib
import cgi

from kiwi.ui.objectlist import Column
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
locale = Locale('plugins')
_ = locale.gettext

def get_value(tab, key):
    if not tab.has_key(key):
        return ''
    return tab[key]

class PluginsAvailableItem(object):

    def __init__(self, infos):
        self.plugin = get_value(infos, 'plugin')
        self.require_version = get_value(infos, 'require_version')
        self.name = get_value(infos, 'name')
        self.author = get_value(infos, 'author')
        self.version = get_value(infos, 'version')
        self.description = get_value(infos, 'description')
        self.enabled = False


class PluginsView(PidaGladeView):

    gladefile = 'plugins-manager'
    locale = locale
    label_text = _('Plugins manager')
    icon_name = 'applications-system'

    def create_ui(self):
        self.plugins_dir = ''
        self.installed_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, data_type=str,
                expand=True),
            Column('enabled', title=_('Enabled'), data_type=bool),
            ])
        self.available_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, data_type=str,
                expand=True),
            Column('version', title=_('Version'), data_type=str),
            ])

    def can_be_closed(self):
        self.svc.get_action('show_plugins').set_active(False)

    def clear_available(self):
        self.available_list.clear()

    def add_available(self, item):
        self.available_list.append(item)

    def on_notebook__switch_page(self, notebook, pointer, index):
        if index == 1:
            self.svc.fetch_available_plugins()

    def on_available_list__selection_changed(self, ot, item):
        markup = '<b>%s</b>' % cgi.escape(item.name)
        if item.require_version != '':
            markup += '\n<b>%s</b> : %s' % (_('Require PIDA'),
                    cgi.escape(item.require_version))
        if item.version != '':
            markup += '\n<b>%s</b> : %s' % (_('Version'),
                    cgi.escape(item.version))
        if item.author != '':
            markup += '\n<b>%s</b> : %s' % (_('Author'),
                    cgi.escape(item.author))
        self.available_title.set_markup(markup)

        self.available_description.get_buffer().set_text(item.description)

    def get_markup(self, item, name, key):
        return ''

class PluginsActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_plugins',
            TYPE_TOGGLE,
            _('Plugins manager'),
            _('Show the plugins manager'),
            'applications-system',
            self.on_show_plugins,
            ''
        )

    def on_show_plugins(self, action):
        if action.get_active():
            self.svc.show_plugins()
        else:
            self.svc.hide_plugins()

class PluginsCommandsConfig(CommandsConfig):

    # Are either of these commands necessary?
    def get_view(self):
        return self.svc.get_view()

    def present_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_view())

class Plugins(Service):
    """ Plugins manager service """

    actions_config = PluginsActionsConfig
    rpc_url = 'http://pida.co.uk/community/RPC2'

    def pre_start(self):
        self._view = PluginsView(self)
        self.task = None

    def show_plugins(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_plugins(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def fetch_available_plugins(self):
        if self.task:
            self.task.stop()

        self._view.clear_available()
        def add_in_list(list):
            self._view.add_available(PluginsAvailableItem(list))
        self.task = GeneratorTask(self._fetch_available_plugins,
                add_in_list)
        self.task.start()

    def _fetch_available_plugins(self):
        proxy = xmlrpclib.ServerProxy(self.rpc_url)
        list = proxy.plugins.list()
        for item in list:
            yield item

    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)


Service = Plugins

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
