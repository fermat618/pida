# -*- coding: utf-8 -*-
"""
    Service Loader
    ~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import sys

from pida.core.service import Service
from pida.core.environment import library

# log
import logging
log = logging.getLogger('pida.servicemanager')
# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class ServiceLoadingError(ImportError):
    """An error loading a service"""

class ServiceModuleError(ServiceLoadingError):
    """No Service class in service module"""

class ServiceDependencyError(ServiceLoadingError):
    """Service does not have the necessary dependencies to start"""


class ServiceLoader(object):
    """Manages loading plugin packages from within a given package"""

    def __init__(self, package, test_file='service.pida'):
        self._test_file = test_file
        self.package = package
        self._path = package.__path__
        self._name = package.__name__

    def unload(self, name):
        """
        unload a plugin module
        """
        del_name = getattr(self.package, name).__name__
        delattr(self.package, name)
        for name in list(sys.modules):
            if name.startswith(del_name):
                del sys.modules[name]


    def get_all(self):
        classes = []
        for name in self._find_all():
            try:
                classes.append(self.get_one(name))
            except ImportError, e:
                log.exception(e)
        classes.sort(key=Service.sort_key)
        return classes

    def get_one(self, name):
        module = '.'.join([self._name, name, name])
        try:
            module = __import__(module, fromlist=['*'], level=0)
        except ImportError, e:
            log.exception(e)
            raise ServiceModuleError(module), None, None
        self._register_service_env(module)

        try:
            service = module.Service
            service.__path__ = os.path.dirname(module.__file__) #XXX: hack
            service.__loader__ = self
            return service
        except AttributeError, e:

            raise ServiceModuleError(module.__name__), None, None


    def get_all_service_files(self):
        for base in self._path:
            for name in self._find_of_dir(base):
                yield name, self._servicefile_path(base, name)

    def _find_of_dir(self, path):
        for name in os.listdir(path):
            if self._has_servicefile(path, name):
                yield name

    def _find_all(self):
        for base in self._path:
            for name in self._find_of_dir(base):
                yield name

    def _servicefile_path(self, base, name):
        return os.path.join(base, name, self._test_file)

    def _has_servicefile(self, base,  name):
        return os.path.exists(self._servicefile_path(base, name))

    def _register_service_env(self, module):
        service_path = os.path.dirname(module.__file__)
        for name in 'glade', 'uidef', 'pixmaps', 'data':
            path = os.path.join(service_path, name)
            if os.path.isdir(path):
                library.add_global_resource(name, path)


class ServiceManager(object):

    def __init__(self, boss, update_progress=None):
        from pida import plugins, services, editors
        if update_progress:
            self.update_progress = update_progress
        self._boss = boss
        self.started = False
        self._services = ServiceLoader(services, '__init__.py')
        self._plugins = ServiceLoader(plugins)
        self._editors = ServiceLoader(editors, '__init__.py')
        self._reg = {}

    def get_service(self, name):
        return self._reg[name]

    def __iter__(self):
        return self._reg.itervalues()

    def __len__(self):
        return len(self._reg)

    def get_services(self):
        return sorted(self, key=Service.sort_key)

    def get_plugins(self):
        return [s for s in self if not s.__module__.startswith('pida.services')]

    def get_services_not_plugins(self):
        return [s for s in self if s.__module__.startswith('pida.services')]

    def activate_services(self):
        self._register_services()
        self._create_services()
        self._subscribe_services()
        self._pre_start_services()

    def start_plugin(self, name):
        plugin_class = self._plugins.get_one(name)
        if plugin_class is None:
            log.error('Unable to load plugin %s' % name)
            return

        #XXX: test this more roughly
        plugin = plugin_class(self._boss)
        try:
            if hasattr(plugin, 'started'):
                log.error("plugin.started shouldn't be set by %r", plugin)

            plugin.started = False # not yet started

            #XXX: unregister?
            pixmaps_dir = os.path.join(plugin.__path__, 'pixmaps')
            if os.path.exists(pixmaps_dir):
                self._boss._icons.register_file_icons_for_directory(pixmaps_dir)
            self._register(plugin)
            try:
                try:
                    plugin.create_all()

                    #stop_components will handle
                    plugin.subscribe_all()

                    #XXX: what to do with unrolling those
                    plugin.pre_start()
                    plugin.start()
                    assert plugin.started is False # this shouldn't change
                    plugin.started = True
                    return plugin
                except:
                    log.debug(_('Stop broken components'))
                    plugin.stop_components()
                    raise
            except:
                del self._reg[name]
                raise

        except Exception, e:
            log.exception(e)
            log.error(_('Could not load plugin %s'), name)
            self._plugins.unload(name)
            raise ServiceLoadingError(name)


    def stop_plugin(self, name):
        plugin = self.get_service(name)
        # Check plugin is a plugin not a service
        if plugin in self.get_plugins():
            plugin.log.debug('Stopping')
            plugin.destroy()

            del self._reg[name]
            self._plugins.unload(name)
        else:
            log.error('ServiceManager: Cannot stop services')
        return plugin

    def _register_services(self):
        # len of self is not yet available
        classes = self._services.get_all()
        pp = 20.0 / len(classes)
        for i, service in enumerate(classes):
            service_instance = service(self._boss)
            #XXX: check for started
            service.started = False
            self._register(service_instance)
            self.update_progress((i + 1) * pp, _("Register Components"))

    def _register(self, service):
        self._reg[service.get_name()] = service

    def _create_services(self):
        pp = 10.0 / len(self)
        for i, svc in enumerate(self.get_services()):
            svc.log.debug('Creating Service')
            svc.create_all()
            self.update_progress(20 + (i + 1) * pp, _("Creating Components"))

    def _subscribe_services(self):
        pp = 10.0 / len(self)
        for i, svc in enumerate(self.get_services()):
            svc.log.debug('Subscribing Service')
            svc.subscribe_all()
            self.update_progress(30 + (i + 1) * pp, _("Subscribing Components"))

    def _pre_start_services(self):
        pp = 20.0 / len(self)
        for i, svc in enumerate(self.get_services()):
            svc.log.debug('Pre Starting Service')
            svc.pre_start()
            self.update_progress(40 + (i + 1) * pp, _("Prepare Components"))

    def start_services(self):
        pp = 40.0 / len(self)
        for i, svc in enumerate(self.get_services()):
            svc.log.debug('Starting Service')
            svc.start()
            #XXX: check if its acceptable here
            svc.started = True
            self.update_progress(60 + (i + 1) * pp, _("Start Components"))
        self.started = True

    def get_available_editors(self):
        return self._editors.get_all()

    def get_editor(self, name):
        return self._editors.get_one(name)

    def activate_editor(self, name):
        self.load_editor(name)
        self.editor.create_all()
        self.editor.subscribe_all()
        self.editor.pre_start()

    def start_editor(self):
        self._register(self.editor)
        self.editor.start()
        self.editor.started = True
        self.update_progress(98, _("Start Editor"))

    def load_editor(self, name):
        assert not hasattr(self, 'editor'), "can't load a second editor"
        editor = self._editors.get_one(name)
        self.editor = editor(self._boss)
        self.editor.started = False
        self._reg[name] = self.editor
        return self.editor

    def stop(self, force=False):
        for svc in self:
            # in force mode we down't care about the return value.
            if not svc.pre_stop() and not force:
                log.info('Shutdown prevented by: %s', svc.get_name())
                return False

        for svc in self:
            # real stop all services
            svc.stop()

        return True

    def _get_update(self):
        if hasattr(self, "_update_progress"):
            return self._update_progress
        else:
            def update_progress(percent, what):
                pass
            return update_progress
    def _set_update(self, value):
        if value:
            self._update_progress = value
        else:
            try:
                del self._update_progress
            except AttributeError:
                pass
    update_progress = property(_get_update, _set_update)


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
