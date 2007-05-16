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
import gobject
import tarfile
import os
import base64
import shutil

from kiwi.ui.objectlist import Column
from pida.ui.views import PidaGladeView
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, OTypeInteger
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall
from pida.core.servicemanager import ServiceLoader

from pida.utils.web import fetch_url
from pida.utils.configobj import ConfigObj

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

def get_value(tab, key):
    if not tab.has_key(key):
        return ''
    return tab[key]

def walktree(top = ".", depthfirst = True, skipped_directory = []):
    """Walk the directory tree, starting from top. Credit to Noah Spurrier and Doug Fort."""
    import os, stat
    names = os.listdir(top)
    if not depthfirst:
        yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            if name in skipped_directory:
                continue
            for (newtop, children) in walktree (os.path.join(top, name),
                    depthfirst, skipped_directory):
                yield newtop, children
    if depthfirst:
        names = [name for name in names if name not in skipped_directory]
        yield top, names

class PluginsItem(object):

    def __init__(self, infos, directory=None):
        self.plugin = get_value(infos, 'plugin')
        self.require_pida = get_value(infos, 'require_pida')
        self.name = get_value(infos, 'name')
        self.author = get_value(infos, 'author')
        self.version = get_value(infos, 'version')
        self.description = get_value(infos, 'description')
        self.category = get_value(infos, 'category')
        self.url = get_value(infos, 'url')
        self.depends = get_value(infos, 'depends')
        self.directory = directory

class PluginsEditItem(object):

    def __init__(self, key, name, value):
        self.key = key
        self.name = name
        self.value = value

class PluginsEditView(PidaGladeView):

    gladefile = 'plugins-edit'
    locale = locale
    label_text = _('Edit a plugin')
    icon_name = gtk.STOCK_EXECUTE

    def create_ui(self):
        self.attr_list.set_columns([
            Column('name', title=_('Name'), data_type=str),
            Column('value', title=_('Value'), data_type=str, editable=True,
                expand=True),
            ])

    def set_item(self, item):
        self.item = item
        if item is None:
            self.attr_list.clear()
            return
        list = []
        list.append(PluginsEditItem('plugin',
            _('Name'), item.plugin))
        list.append(PluginsEditItem('name',
            _('Plugin long name'), item.name))
        list.append(PluginsEditItem('author',
            _('Author'), item.author))
        list.append(PluginsEditItem('version',
            _('Version'), item.version))
        list.append(PluginsEditItem('depends',
            _('Depends'), item.depends))
        list.append(PluginsEditItem('require_pida',
            _('Require PIDA version'), item.require_pida))
        list.append(PluginsEditItem('category', _('Category'),
            item.category))
        list.append(PluginsEditItem('description', _('Description'),
            item.description))
        self.attr_list.add_list(list, clear=True)

    def on_attr_list__cell_edited(self, w, item, value):
        setattr(self.item, getattr(item, 'key'), getattr(item, 'value'))
        self.svc._view.update_publish_infos()
        self.svc.write_informations(self.item)

    def on_close_button__clicked(self, w):
        self.svc.hide_plugins_edit()


class PluginsView(PidaGladeView):

    gladefile = 'plugins-manager'
    locale = locale
    label_text = _('Plugins manager')
    icon_name = gtk.STOCK_EXECUTE

    def create_ui(self):
        self._current = None
        self.item = None
        self.installed_item = None
        self.plugins_dir = ''
        self.first_start = True
        self.installed_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, data_type=str,
                expand=True),
            Column('version', title=_('Version'), data_type=str),
            ])
        self.available_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, data_type=str,
                expand=True),
            Column('version', title=_('Version'), data_type=str),
            ])

    def can_be_closed(self):
        self.svc.get_action('show_plugins').set_active(False)

    def clear_installed(self):
        self.installed_list.clear()

    def add_installed(self, item):
        self.installed_list.append(item)

    def clear_available(self):
        self.available_list.clear()

    def add_available(self, item):
        self.available_list.append(item)

    def on_available_refresh_button__clicked(self, w):
        self.svc.fetch_available_plugins()

    def on_notebook__switch_page(self, notebook, pointer, index):
        if index == 1:
            if self.first_start:
                self.first_start = False
                self.svc.fetch_available_plugins()
        else:
            self.svc.update_installed_plugins()

    def on_available_list__selection_changed(self, ot, item):
        self._current = item

        # no item, clear fields
        if item is None:
            self.available_title.set_text(_('No plugin selected'))
            self.available_description.get_buffer().set_text('')
            self.available_install_button.set_sensitive(False)
            return

        # fill fields
        markup = self.svc._get_item_markup(item)
        self.available_title.set_markup(markup)
        self.available_description.get_buffer().set_text(item.description)
        self.available_install_button.set_sensitive(True)

    def on_installed_list__selection_changed(self, ot, item):
        self.installed_item = item

        # no item, clear fields
        if item is None:
            self.installed_title.set_text(_('No plugin selected'))
            self.installed_description.get_buffer().set_text('')
            self.installed_delete_button.set_sensitive(False)
            return

        # fill fields
        markup = self.svc._get_item_markup(item)
        self.installed_title.set_markup(markup)
        self.installed_description.get_buffer().set_text(item.description)
        self.installed_delete_button.set_sensitive(True)

    def on_publish_directory__selection_changed(self, w):
        directory = self.publish_directory.get_filename()
        if self.svc.is_plugin_directory(directory):
            self.item = self.svc.read_plugin_informations(directory)
            self.item.directory = directory
            self.publish_button.set_sensitive(True)
            self.publish_edit_button.set_sensitive(True)
            self.svc._viewedit.set_item(self.item)
            self.update_publish_infos()
        else:
            self.item = None
            self.publish_button.set_sensitive(False)
            self.publish_edit_button.set_sensitive(False)
            self.svc._viewedit.set_item(None)
            self.update_publish_infos()

    def on_available_install_button__clicked(self, w):
        if not self._current:
            return
        self.svc.download(self._current)

    def on_publish_button__clicked(self, w):
        directory = self.publish_directory.get_filename()
        login = self.publish_login.get_text()
        password = self.publish_password.get_text()
        self.svc.upload(directory, login, password)

    def on_installed_delete_button__clicked(self, w):
        if not self.installed_item:
            return
        if not self.installed_item.directory:
            return
        if not os.path.exists(self.installed_item.directory):
            return
        shutil.rmtree(self.installed_item.directory, True)
        self.svc.update_installed_plugins()

    def on_publish_edit_button__clicked(self, w):
        self.svc.show_plugins_edit()

    def update_publish_infos(self):
        if self.item is None:
            self.publish_infos.set_text('')
            self.publish_description.get_buffer().set_text('')
            return
        self.publish_infos.set_markup(self.svc._get_item_markup(self.item))
        self.publish_description.get_buffer().set_text(self.item.description)

    def start_pulse(self, title):
        self._pulsing = True
        self.available_progress.set_text(title)
        self.available_progress.show_all()
        self.available_refresh_button.set_sensitive(False)
        gobject.timeout_add(100, self._pulse)

    def stop_pulse(self):
        self.available_progress.hide()
        self.available_refresh_button.set_sensitive(True)
        self._pulsing = False

    def _pulse(self):
        self.available_progress.pulse()
        return self._pulsing

    def start_publish_pulse(self, title):
        self._publish_pulsing = True
        self.publish_progress.set_text(title)
        self.publish_progress.show_all()
        self.publish_button.set_sensitive(False)
        self.publish_edit_button.set_sensitive(False)
        gobject.timeout_add(100, self._publish_pulse)

    def stop_publish_pulse(self):
        self.publish_progress.hide()
        self.publish_button.set_sensitive(True)
        self.publish_edit_button.set_sensitive(True)
        self._publish_pulsing = False

    def _publish_pulse(self):
        self.publish_progress.pulse()
        return self._publish_pulsing


class PluginsActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_plugins',
            TYPE_TOGGLE,
            _('Plugins manager'),
            _('Show the plugins manager'),
            gtk.STOCK_EXECUTE,
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
        self._viewedit = PluginsEditView(self)
        self.task = None
        self.plugin_path = self.boss._env.get_plugins_directory()

    def start(self):
        self.update_installed_plugins(start=True)

    def show_plugins(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_plugins(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def show_plugins_edit(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._viewedit)

    def hide_plugins_edit(self):
        self.boss.cmd('window', 'remove_view', view=self._viewedit)

    def update_installed_plugins(self, start=False):
        service_loader = ServiceLoader()
        self._view.clear_installed()
        l_installed = service_loader.get_all_services([self.plugin_path])

        for item in l_installed:
            # read config
            plugin_item = self.read_plugin_informations(
                    servicefile=item.servicefile_path)
            self._view.add_installed(plugin_item)

            # start mode
            if start:
                plugin_path = os.path.dirname(item.servicefile_path)
                self.boss._sm.start_plugin(plugin_path)

    def fetch_available_plugins(self):
        if self.task:
            self.task.stop()

        def add_in_list(list):
            self._view.add_available(PluginsItem(list))

        def stop_pulse():
            self._view.stop_pulse()

        self._view.clear_available()
        self.task = GeneratorTask(self._fetch_available_plugins,
                add_in_list, stop_pulse)
        self.task.start()

    def _fetch_available_plugins(self):
        self._view.start_pulse(_('Download available plugins'))
        proxy = xmlrpclib.ServerProxy(self.rpc_url)
        list = proxy.plugins.list()
        for item in list:
            yield item

    def download(self, item):
        if not item.url or item.url == '':
            return
        self._view.start_pulse(_('Download %s') % item.name)
        def download_complete(url, content):
            self._view.stop_pulse()
            if content != '':
                self.install(item, content)
        fetch_url(item.url, download_complete)

    def install(self, item, content):
        # write plugin
        filename = os.path.join(self.plugin_path, os.path.basename(item.url))
        file = open(filename, 'wb')
        file.write(content)
        file.close()

        # extract him
        tar = tarfile.open(filename, 'r:gz')
        for tarinfo in tar:
            tar.extract(tarinfo, path=self.plugin_path)
        tar.close()
        os.unlink(filename)

        # start service
        plugin_path = os.path.join(self.plugin_path, item.plugin)
        self.boss._sm.start_plugin(plugin_path)

    def upload(self, directory, login, password):
        # first, check for a service.pida file
        if not self.is_plugin_directory(directory):
            return

        # extract plugin name
        plugin = os.path.basename(directory)

        # get filelist
        self._view.start_publish_pulse('Listing files')
        skipped_directory = [ '.svn', 'CVS' ]
        list = []
        for top, names in walktree(top=directory,
                skipped_directory=skipped_directory):
            list.append(top)
            for name in names:
                list.append(os.path.join(top, name))

        # remove some unattended files
        skipped_extentions = [ 'swp', 'pyc' ]
        list = [ name for name in list if name.split('.')[-1] not in skipped_extentions ]

        # make tarfile
        self._view.start_publish_pulse('Building package')
        filename = os.tmpnam()
        tar = tarfile.open(filename, 'w:gz')
        for name in list:
            arcname = os.path.join(plugin, name[len(directory):])
            tar.add(name, arcname=arcname, recursive=False)
        tar.close()

        def upload_do(login, password, filename):
            try:
                try:
                    file = open(filename, 'rb')
                    data = file.read()
                    file.close()
                    proxy = xmlrpclib.ServerProxy(self.rpc_url)
                    code = proxy.plugins.push(login, password,
                            base64.b64encode(data))
                    print _('Community response : '), code
                except xmlrpclib.Fault, fault:
                    print _('Error while posting plugin : '), fault
            finally:
                os.unlink(filename)
                self._view.stop_publish_pulse()

        self._view.start_publish_pulse('Upload to community website')
        task = AsyncTask(upload_do)
        task.start(login, password, filename)

    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)

    def is_plugin_directory(self, directory):
        return os.path.exists(os.path.join(directory, 'service.pida'))

    def read_plugin_informations(self, directory=None, servicefile=None):
        if servicefile is None:
            servicefile = os.path.join(directory, 'service.pida')
        config = ConfigObj(servicefile)
        return PluginsItem(config['plugin'],
                directory=os.path.dirname(servicefile))

    def write_informations(self, item):
        if not item.directory:
            return
        config = ConfigObj(os.path.join(item.directory, 'service.pida'))
        section = config['plugin']
        for key in [ 'plugin', 'name', 'author', 'version', 'require_pida',
                'depends', 'category', 'description' ]:
            section[key] = getattr(item, key)
        config.write()

    def _get_item_markup(self, item):
        markup = '<b>%s</b>' % cgi.escape(item.name)
        if item.version != '':
            markup += '\n<b>%s</b> : %s' % (_('Version'),
                    cgi.escape(item.version))
        if item.author != '':
            markup += '\n<b>%s</b> : %s' % (_('Author'),
                    cgi.escape(item.author))
        if item.category != '':
            markup += '\n<b>%s</b> : %s' % (_('Category'),
                    cgi.escape(item.category))
        if item.depends != '':
            markup += '\n<b>%s</b> : %s' % (_('Depends'),
                    cgi.escape(item.depends))
        if item.require_pida != '':
            markup += '\n<b>%s</b> : %s' % (_('Require PIDA'),
                    cgi.escape(item.require_pida))
        return markup


Service = Plugins

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
