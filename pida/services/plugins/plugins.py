# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project
#XXX: rework
"""
    pida.services.plugins
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies ui components for plugin management

    .. deprecated::

        the current plugin updating mechanism is kinda borked
        it needs a reimplementation when creating a new homepage

    :license: GPL2 or later
"""
from __future__ import with_statement
import StringIO


import gtk
import cgi
import gobject
import tarfile
import os
import shutil
import pida.plugins

from pygtkhelpers.ui.objectlist import Column
from pida.ui.views import PidaGladeView, WindowConfig
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.features import FeaturesConfig
from pida.core.options import OptionsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE
from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall
from pida.core.servicemanager import ServiceLoader, ServiceLoadingError

from pida.core.environment import plugins_dir

from pida.utils.web import fetch_url

from . import metadata
from . import packer
from . import downloader

# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext



class PluginsEditItem(object):

    def __init__(self, key, name, value):
        self.key = key
        self.name = name
        self.value = value

class PluginsEditView(PidaGladeView):

    key = 'plugins.editor'

    gladefile = 'plugins_edit'
    locale = locale
    label_text = _('Edit a plugin')
    icon_name = gtk.STOCK_EXECUTE

    edit_items = (
        ('name', _('Plugin name')),
        ('author', _('Author')),
        ('version', _('Version')),
        ('depends', _('Dependencies')),
        ('category', _('Category')),
        ('description', _('Description')),
    )

    def create_ui(self):
        self.attr_list.set_columns([
            Column('name', title=_('Name')),
            Column('value', title=_('Value'),
                   editable=True,
                   expand=True),
            ])

    def set_item(self, item):
        self.item = item
        if item is None:
            self.attr_list.clear()
            return
        listing = [
            PluginsEditItem(key, name, item.get(key))
            for key, name in self.edit_items
        ]
        self.attr_list.add_list(listing, clear=True)

    def on_attr_list__item_changed(self, w, item, attr, value):
        setattr(self.item, getattr(item, 'key'), getattr(item, 'value'))
        self.svc._view.update_publish_infos()
        self.svc.write_informations(self.item)

    def on_close_button__clicked(self, w):
        self.svc.hide_plugins_edit()


class PluginsView(PidaGladeView):

    key = 'plugins.view'

    gladefile = 'plugins_manager'
    locale = locale
    label_text = _('Plugins manager')
    icon_name = gtk.STOCK_EXECUTE

    def create_ui(self):
        self._current = None
        self.item = None
        self.installed_item = None
        self.first_start = True
        self.installed_list.set_columns([
            Column('name', title=_('Plugin'), sorted=True, expand=True),
            Column('enabled', title=_('Enabled'), type=bool,
                              editable=True, use_checkbox=True)
            ])
        self.available_list.set_columns([
            Column('markup', title=_('Plugin'), sorted=True,
                expand=True, use_markup=True),
            Column('version', title=_('Version')),
            ])
        #XXX: reenable ui publisher after making a newui
    
        self.notebook.remove_page(2)

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

    def on_available_list__selection_changed(self,  ot):
        self._current = item = ot.selected_item

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

    def on_installed_list__selection_changed(self, ot):
        self.installed_item = item = ot.selected_item

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

    def on_installed_list__item_changed(self, w, item, attr, value):
        if attr != 'enabled': 
            return
        if item.enabled: 
            success = self.svc.start_plugin(item.plugin)
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
        PluginsWindowConfig.action = self.create_action(
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
            'publish_to',
            _('Webservice Url'),
            str,
            '',
            _('URL of Webservice to download plugins'),
            )

        self.create_option(
            'check_for_updates',
            _('Check updates'),
            bool,
            True,
            _('Check for plugins updates in background'),
            self.on_check_for_updates)

        self.create_option(
            'start_list',
            _('Start plugin list'),
            list, 
            [], 
            _('List of plugin to start'),
            safe=False,
            workspace=True
            )


    def on_check_for_updates(self, option):
        self.svc.check_for_updates(option.value)


class PluginsEvents(EventsConfig):

    def create(self):
        self.publish('plugin_started', 'plugin_stopped')


class PluginsWindowConfig(WindowConfig):
    key = PluginsView.key
    label_text = PluginsView.label_text

class PluginsFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            PluginsWindowConfig)

class Plugins(Service):
    """ Plugins manager service """

    actions_config = PluginsActionsConfig
    options_config = PluginsOptionsConfig
    events_config = PluginsEvents
    features_config = PluginsFeaturesConfig

    def pre_start(self):
        self._check = False
        self._check_notify = False
        self._check_event = False
        #XXX: we should really use the real one at some point
        self._loader = ServiceLoader(pida.plugins)
        self._view = PluginsView(self)
        self._viewedit = PluginsEditView(self)
        self.task = None

    def start(self):
        self.update_installed_plugins(start=True)
        self.check_for_updates(self.opt('check_for_updates'))

    def show_plugins(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        self.update_installed_plugins()

    def start_plugin(self, name):
        try:
            plugin = self.boss.start_plugin(name)
            self.emit('plugin_started', plugin=plugin)
            self.boss.cmd('notify', 'notify', title=_('Plugins'),
                data = _('Started %(plugin)s plugin' % {
                    'plugin':plugin.get_label()
                }))
            return True
        except ServiceLoadingError, e:
            #XXX: support a ui traceback browser?
            self.boss.cmd('notify', 'notify', title=_('Plugins'),
                data = _('Could not start plugin: %(name)s\n%(error)s' % 
                    {'error':str(e), 'name':name}))
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
            start_list = self.opt('start_list')
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
                try:
                    plugin = self.boss.start_plugin(service_name)
                    self.emit('plugin_started', plugin=plugin)
                    plugin_item.enabled = True
                except ServiceLoadingError, e:
                    self.log.error(e)
            else:
                self._view.add_installed(plugin_item)

    def fetch_available_plugins(self):
        if self.task:
            self.task.stop()

        def add_in_list(data, isnew):
            if isnew and self._check_notify:
                self.boss.cmd('notify', 'notify', 
                              title=_('Plugins'),
                    data=_('Version %(version)s of %(plugin)s is available !') \
                            % data)
            self._view.add_available(data)

        def stop_pulse():
            self._check_notify = False
            self._view.stop_pulse()

        self._view.clear_available()
        self._view.start_pulse( _('Download available plugins'))
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
        #XXX: DAMMIT this is in a worker thread ?!?!
        try:
            items = downloader.find_latest_metadata(
                    'http://packages.pida.co.uk/simple/'
            )
            for item in items:
                self.log.debug('found plugin %s', item.name)
                inst = None
                isnew = False
                for plugin in installed_list:
                    #XXX: module is weird, maybe change rpc
                    if plugin.plugin == item.plugin:
                        inst = plugin
                if inst is not None:
                    isnew = (inst.version != item.version)
                yield item, isnew
        except Exception, e:
            print e
            raise

    def download(self, item):
        if not item.url:
            return
        self._view.start_pulse(_('Download %s') % item.name)
        def download_complete(url, content):
            self._view.stop_pulse()
            if content:
                self.install(item, content)
        fetch_url(item.url, download_complete)

    def install(self, item, content):
        item.base = plugins_dir
        item.directory = os.path.join(plugins_dir, item.plugin)

        # this will gracefully ignore not installed plugins
        self.delete(item, force=True)
        
        io = StringIO.StringIO(content)
        tar = tarfile.TarFile.gzopen(None, fileobj=io)
        tar.extractall(plugins_dir)
        
        # start service
        self.start_plugin(item.plugin)
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
        # XXX: get smarter for more tricky plugins
        # (external processes, java, ...)

        # extract plugin name
        plugin = os.path.basename(directory)
        base = os.path.dirname(directory)
        # first, check for a service.pida file
        if not metadata.is_plugin(base, plugin):
            return

        def notify(text):
            gcall(self._view.start_publish_pulse, text)
        # get filelist
        def upload_do():
            try:
                packer.upload_plugin(
                    base, plugin,
                    self.opt('publish_to'),
                    login, password,
                    notify)
                #XXX: stuff
                gcall(self.boss.cmd, 'notify', 'notify',
                     title=_('Plugins'),
                     data=_('Package upload success !'))
            finally:
                gcall(self._view.stop_publish_pulse)

        self._view.start_publish_pulse('Upload to community website')
        task = AsyncTask(upload_do)
        task.start()

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
        if directory is None:
            directory = os.path.dirname(servicefile)

        plugin = os.path.basename(directory)
        base = os.path.dirname(directory)

        return metadata.from_plugin(base, plugin)

    def write_informations(self, item):
        if item.plugin and item.base:
            metadata.serialize(item.base, item.plugin, item)


    def save_running_plugin(self):
        list = [
            plugin.get_name() 
            for plugin in self.boss.get_plugins()
        ]
        self.set_opt('start_list', list)

    def _get_item_markup(self, item):
        markup = '<b>%s</b>' % cgi.escape(item.name or str(item))
        if item.version:
            markup += '\n<b>%s</b> : %s' % (_('Version'),
                    cgi.escape(item.version))
        if item.author:
            markup += '\n<b>%s</b> : %s' % (_('Author'),
                    cgi.escape(item.author))
        if item.category:
            markup += '\n<b>%s</b> : %s' % (_('Category'),
                    cgi.escape(item.category))
        if item.depends:
            markup += '\n<b>%s</b> : %s' % (_('Depends'),
                    cgi.escape(item.depends))
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
            # we don't fetch when starting the service to reduce
            # startup time
            self._check_for_updates(fetch=False)
            return

    def _check_for_updates(self, fetch=True):
        self._check_event = False
        if not self._check:
            return
        self._check_notify = True
        if fetch:
            self.fetch_available_plugins()
        # relaunch event in 30 minutes
        if not self._check_event:
            gobject.timeout_add(30 * 60 * 1000, self._check_for_updates)
            self._check_event = True


Service = Plugins

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
