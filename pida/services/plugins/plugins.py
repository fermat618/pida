# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

"""
    pida.services.plugins
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies ui components for plugin management

    .. deprecated::

        the current plugin updating mechanism is kinda borked
        it needs a reimplementation when creating a new homepage

    :license: GPL2 or later
"""

import gtk
import xmlrpclib
import cgi
import gobject
import tarfile
import os
import base64
import shutil
import httplib
import pida.plugins

from kiwi.ui.objectlist import Column
from pida import PIDA_VERSION
from pida.ui.views import PidaGladeView
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, OTypeBoolean
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall
from pida.core.servicemanager import ServiceLoader, ServiceLoadingError
from pida.core.options import OptionItem, manager, OTypeStringList, OTypeString

from pida.core.environment import plugins_dir

from pida.utils.web import fetch_url
from pida.utils.configobj import ConfigObj
from pida.utils.path import walktree

# consts
PLUGIN_RPC_URL = 'http://pida.co.uk/RPC2'

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

def get_value(tab, key):
    return tab.get(key, None)

# http://docs.python.org/lib/xmlrpc-client-example.html
class ProxiedTransport(xmlrpclib.Transport):

    def __init__(self, proxy):
        self.proxy = proxy

    def make_connection(self, host):
        self.realhost = host
        return httplib.HTTP(self.proxy)

    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", 'http://%s%s' % (self.realhost, handler))

    def send_host(self, connection, host):
        connection.putheader('Host', self.realhost)

def create_transport():
    if 'http_proxy' in os.environ:
        host = os.environ['http_proxy']
        return ProxiedTransport(host)
    else:
        return xmlrpclib.Transport()

class PluginsItem(object):

    def __init__(self, infos, directory=None, enabled=False, isnew=False):
        self.isnew = isnew
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
        self.enabled = enabled

    @property
    def markup(self):
        if self.isnew:
            return '<span color="red"><b>!N</b></span> %s' % self.name
        return self.name


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
        self.first_start = True
        self.installed_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, data_type=str,
                expand=True),
            Column('enabled', title=_('Enabled'), data_type=bool,
                editable=True)
            ])
        self.available_list.set_columns([
            Column('markup', title=_('Plugin'), sorted=True, data_type=str,
                expand=True, use_markup=True),
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

    def after_notebook__switch_page(self, notebook, pointer, index):
        if index == 1:
            if self.first_start:
                self.first_start = False
                def _fetch():
                    gcall(self.svc.fetch_available_plugins)
                gobject.idle_add(_fetch)
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

    def on_installed_list__cell_edited(self, w, item, value):
        if value != 'enabled':
            return
        if not item.directory:
            return
        if item.enabled:
            success = self.svc.start_plugin(item.directory)
            item.enabled = success
        else:
            self.svc.stop_plugin(item.plugin)
        self.svc.save_running_plugin()

    def on_publish_button__clicked(self, w):
        directory = self.publish_directory.get_filename()
        login = self.publish_login.get_text()
        password = self.publish_password.get_text()
        self.svc.upload(directory, login, password)

    def on_installed_delete_button__clicked(self, w):
        self.svc.delete(self.installed_item)

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


class PluginsOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'rpc_url',
            _('Webservice Url'),
            OTypeString,
            PLUGIN_RPC_URL,
            _('URL of Webservice to download plugins'),
            self.on_rpc_url)

        self.create_option(
            'check_for_updates',
            _('Check updates'),
            OTypeBoolean,
            True,
            _('Check for plugins updates in background'),
            self.on_check_for_updates)

    def on_rpc_url(self, client, id, entry, option):
        self.svc.rpc_url = option.get_value()

    def on_check_for_updates(self, client, id, entry, option):
        self.svc.check_for_updates(option.get_value())


class PluginsEvents(EventsConfig):

    def create(self):
        self.publish('plugin_started', 'plugin_stopped')


class Plugins(Service):
    """ Plugins manager service """

    actions_config = PluginsActionsConfig
    options_config = PluginsOptionsConfig
    events_config = PluginsEvents
    rpc_url = PLUGIN_RPC_URL

    def pre_start(self):
        self._check = False
        self._check_notify = False
        self._check_event = False
        self._loader = ServiceLoader(pida.plugins)
        self._view = PluginsView(self)
        self._viewedit = PluginsEditView(self)
        self.task = None
        self._start_list = OptionItem('plugins', 'start_list', _('Start plugin list'),
                OTypeStringList, [], _('List of plugin to start'), None)
        manager.register_option(self._start_list)

    def start(self):
        self.rpc_url = self.opt('rpc_url')
        self.update_installed_plugins(start=True)
        self.check_for_updates(self.get_option('check_for_updates').get_value())

    def show_plugins(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        self.update_installed_plugins()

    def start_plugin(self, name):
        try:
            plugin = self.boss.start_plugin(name)
            self.emit('plugin_started', plugin=plugin)
            self.boss.cmd('notify', 'notify', title=_('Plugins'),
                data = _('Started %(plugin)s plugin' % {'plugin':plugin.get_label()}))
            return True
        except ServiceLoadingError, e:
            self.boss.cmd('notify', 'notify', title=_('Plugins'),
                data = _('Could not start plugin: %(name)s\n%(error)s' % 
                    {'error':str(e), 'plugin_path':name}))
            return False

    def stop_plugin(self, name):
        plugin = self.boss.stop_plugin(name)
        self.emit('plugin_stopped', plugin=plugin)
        self.boss.cmd('notify', 'notify', title=_('Plugins'),
            data = _('Stopped %(plugin)s plugin' % {'plugin':plugin.get_label()}))

    def hide_plugins(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def show_plugins_edit(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._viewedit)

    def hide_plugins_edit(self):
        self.boss.cmd('window', 'remove_view', view=self._viewedit)

    def update_installed_plugins(self, start=False):
        self._view.clear_installed()
        l_installed = list(self._loader.get_all_service_files())
        if start:
            start_list = manager.get_value(self._start_list)
        running_list = [plugin.get_name() for plugin in
                self.boss.get_plugins()]

        loading_errors = []

        for service_name, service_file in l_installed:
            # read config
            plugin_item = self.read_plugin_informations(
                    servicefile=service_file)

            if plugin_item.plugin in running_list:
                plugin_item.enabled = True

            # start mode
            if start:
                if service_name not in start_list:
                    continue
                plugin_path = os.path.dirname(service_file)
                plugin_name = os.path.basename(plugin_path)
                try:
                    plugin = self.boss.start_plugin(plugin_name)
                    self.emit('plugin_started', plugin=plugin)
                    plugin_item.enabled = True
                except ServiceLoadingError, e:
                    self.log.error(e)
            else:
                self._view.add_installed(plugin_item)

    def fetch_available_plugins(self):
        if self.task:
            self.task.stop()

        def add_in_list(list, isnew):
            if isnew and self._check_notify:
                self.boss.cmd('notify', 'notify', title=_('Plugins'),
                    data=_('Version %(version)s of %(plugin)s is available !') \
                            % {'version':list['version'], 'plugin':list['plugin']})
            self._view.add_available(PluginsItem(list, isnew=isnew))

        def stop_pulse():
            self._check_notify = False
            self._view.stop_pulse()

        self._view.clear_available()
        self.task = GeneratorTask(self._fetch_available_plugins,
                add_in_list, stop_pulse)
        self.task.start()

    def _fetch_available_plugins(self):
        # get installed items
        l_installed = list(self._loader.get_all_service_files())
        installed_list = []
        for service_name, service_file in l_installed:
            plugin_item = self.read_plugin_informations(
                    servicefile=service_file)
            installed_list.append(plugin_item)

        self._view.start_pulse(_('Download available plugins'))
        try:
            proxy = xmlrpclib.ServerProxy(self.rpc_url,
                                          transport=create_transport())
            plist = proxy.plugins.list({'version': PIDA_VERSION})
            for k in plist:
                item = plist[k]
                inst = None
                isnew = False
                for plugin in installed_list:
                    if plugin.plugin == item['plugin']:
                        inst = plugin
                if inst is not None:
                    isnew = (inst.version != item['version'])
                yield item, isnew
        except:
            pass

    def download(self, item):
        if not item.url or item.url == '':
            return
        self._view.start_pulse(_('Download %s') % item.name)
        def download_complete(url, content):
            self._view.stop_pulse()
            if content:
                self.install(item, content)
        fetch_url(item.url, download_complete)

    def install(self, item, content):
        # write plugin
        plugin_path = os.path.join(plugins_dir, item.plugin)
        filename = os.path.join(plugins_dir, os.path.basename(item.url))
        file = open(filename, 'wb')
        file.write(content)
        file.close()

        # check if we need to stop and remove him
        l_installed = [p[0] for p in
            self._loader.get_all_service_files()]
        item.directory = plugin_path
        if item.plugin in l_installed:
            self.delete(item, force=True)

        # extract him
        tar = tarfile.open(filename, 'r:gz')
        for tarinfo in tar:
            tar.extract(tarinfo, path=plugins_dir)
        tar.close()
        os.unlink(filename)

        # start service
        self.start_plugin(plugins_dir)
        self.boss.cmd('notify', 'notify', title=_('Plugins'),
                data=_('Installation of %s completed') % item.plugin)

    def delete(self, item, force=False):
        if not item:
            return
        if not item.directory:
            return
        if not os.path.exists(item.directory):
            return
        if not force:
            if not self.yesno_dlg(
                _('Are you sure to delete "%s" plugin ?' % item.name)):
                return
        running_list = [plugin.get_name() for plugin in
                self.boss.get_plugins()]
        if item.plugin in running_list:
            self.stop_plugin(item.plugin)
        shutil.rmtree(item.directory, True)
        self.update_installed_plugins()

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
            arcname = plugin + name[len(directory):]
            tar.add(name, arcname=arcname, recursive=False)
        tar.close()

        def upload_do(login, password, plugin, filename):
            try:
                try:
                    file = open(filename, 'rb')
                    data = file.read()
                    file.close()
                    proxy = xmlrpclib.ServerProxy(self.rpc_url,
                                                  transport=create_transport())
                    code = proxy.plugins.push(login, password,
                            plugin, base64.b64encode(data))
                    gcall(self.boss.cmd, 'notify', 'notify',
                            title=_('Plugins'), data=_('Package upload success !'))
                except xmlrpclib.Fault, fault:
                    print _('Error while posting plugin : '), fault
                except:
                    pass
            finally:
                os.unlink(filename)
                self._view.stop_publish_pulse()

        self._view.start_publish_pulse('Upload to community website')
        task = AsyncTask(upload_do)
        task.start(login, password, plugin, filename)

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

    def save_running_plugin(self):
        list = [plugin.get_name() for plugin in self.boss.get_plugins()]
        manager.set_value(self._start_list, list)

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


    def check_for_updates(self, check):
        # already activated, skip
        if self._check and check:
            return

        # disabled:
        if self._check and not check:
            self._check = check
            return

        # enable
        if not self._check and check:
            self._check = check
            # check now
            self._check_for_updates()
            return

    def _check_for_updates(self):
        self._check_event = False
        if not self._check:
            return
        self._check_notify = True
        self.fetch_available_plugins()
        # relaunch event in 30 minutes
        if not self._check_event:
            gobject.timeout_add(30 * 60 * 1000, self._check_for_updates)
            self._check_event = True


Service = Plugins

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
