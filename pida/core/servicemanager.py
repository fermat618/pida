import os, imp

from pida.core.interfaces import IService, IEditor, IPlugin
from pida.core.plugins import Registry

from pida.core.environment import library, environ

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


def sort_services_func(s1, s2):
    return cmp(s1.servicename, s2.servicename)

class ServiceLoadingError(Exception):
    """An error loading a service"""

class ServiceModuleError(ServiceLoadingError):
    """No Service class in service module"""

class ServiceDependencyError(ServiceLoadingError):
    """Service does not have the necessary dependencies to start"""

class ServiceLoader(object):

    def __init__(self, boss=None):
        self.boss = boss

    def get_all_services(self, service_dirs):
        classes = []
        for service_path in self._find_all_service_paths(service_dirs):
            try:
                service_class = self.get_one_service(service_path)
            except ServiceLoadingError, e:
                self.boss.log.error('Service error: %s: %s' %
                                   (e.__class__.__name__, e))
                service_class = None
            if service_class is not None:
                classes.append(service_class)
        classes.sort(sort_services_func)
        return classes

    def get_one_service(self, service_path):
        module = self._load_service_module(service_path)
        if module is not None:
            service_class = self._load_service_class(module)
            if service_class is not None:
                service_class.servicename = module.servicename
                service_class.servicefile_path = module.servicefile_path
                return service_class

    def load_all_services(self, service_dirs, boss):
        services = []
        for service_class in self.get_all_services(service_dirs):
            services.append(self._instantiate_service(service_class, boss))
        services.sort(sort_services_func)
        return services

    def load_one_service(self, service_path, boss):
        service_class = self.get_one_service(service_path)
        if service_class is not None:
            return self._instantiate_service(service_class, boss)

    def get_all_service_files(self, service_dirs):
        for service_path in self._find_all_service_paths(service_dirs):
            yield os.path.basename(service_path), self._get_servicefile_path(service_path)

    def _instantiate_service(self, service_class, boss):
        return service_class(boss)

    def _find_service_paths(self, service_dir):
        for f in os.listdir(service_dir):
            service_path = os.path.join(service_dir, f)
            if self._has_servicefile(service_path):
                yield service_path

    def _find_all_service_paths(self, service_dirs):
        for service_dir in service_dirs:
            if os.path.isdir(service_dir):
                for service_path in self._find_service_paths(service_dir):
                    yield service_path

    def _get_servicefile_path(self, service_path, servicefile_name='service.pida'):
        return os.path.join(service_path, servicefile_name)

    def _has_servicefile(self, service_path):
        return os.path.exists(self._get_servicefile_path(service_path))

    def _load_service_module(self, service_path):
        name = os.path.basename(service_path)
        try:
            fp, pathname, description = imp.find_module(name, [service_path])
        except Exception, e:
            raise ServiceLoadingError('%s: %s' % (name, e))
        try:
            module = imp.load_module(name, fp, pathname, description)
        except ImportError, e:
            raise ServiceDependencyError('%s: %s' % (name, e))
        module.servicename = name
        module.servicefile_path = self._get_servicefile_path(service_path)
        self._register_service_env(name, service_path)
        return module

    def _load_service_class(self, module):
        try:
            service = module.Service
        except AttributeError, e:
            raise ServiceModuleError('Service has no Service class')
        service.servicemodule = module
        return service

    def _register_service_env(self, servicename, service_path):
        for name in ['glade', 'uidef', 'pixmaps', 'data']:
            path = os.path.join(service_path, name)
            if os.path.isdir(path):
                library.add_global_resource(name, path)


class ServiceManager(object):

    def __init__(self, boss):
        self._boss = boss
        self._loader = ServiceLoader(self._boss)
        self._reg = Registry()
        self._plugin_objects = {}

    def get_service(self, name):
        return self._reg.get_singleton(name)

    def get_services(self):
        services = list(self._reg.get_features(IService))
        services.sort(sort_services_func)
        return services

    def get_plugins(self):
        plugins = list(self._reg.get_features(IPlugin))
        plugins.sort(sort_services_func)
        return plugins

    def get_services_not_plugins(self):
        services = self.get_services()
        plugins = self.get_plugins()
        return [s for s in services if s not in plugins]

    def activate_services(self):
        self._register_services()
        self._create_services()
        self._subscribe_services()
        self._pre_start_services()

    def start_plugin(self, plugin_path):
        plugin = self._loader.load_one_service(plugin_path, self._boss)
        pixmaps_dir = os.path.join(plugin_path, 'pixmaps')
        self._boss._icons.register_file_icons_for_directory(pixmaps_dir)
        if plugin is not None:
            self._register_plugin(plugin)
            plugin.create_all()
            plugin.subscribe_all()
            plugin.pre_start()
            plugin.start()
            return plugin
        else:
            self._boss.log.error('Unable to load plugin from %s' % plugin_path)

    def stop_plugin(self, plugin_name):
        plugin = self.get_service(plugin_name)
        if plugin is not None:
            # Check plugin is a plugin not a service
            if plugin in self.get_plugins():
                plugin.log_debug('Stopping')
                plugin.stop_components()
                plugin.stop()
                self._reg.unregister(self._plugin_objects[plugin_name])
                return plugin
            else:
                self._boss.log.error('ServiceManager: Cannot stop services')
        else:
            self._boss.log.error('ServiceManager: Cannot find plugin %s' % plugin_name)

    def _register_services(self):
        for svc in self._loader.load_all_services(
                self._boss.get_service_dirs(), self._boss):
            self._register_service(svc)

    def _register_service(self, service):
        self._reg.register_plugin(
            instance=service,
            singletons=(
                service.servicename,
            ),
            features=(
                IService,
            )
        )

    def _register_plugin(self, plugin):
        plugin_object = self._reg.register_plugin(
            instance=plugin,
            singletons=(
                plugin.servicename,
            ),
            features=(
                IService,
                IPlugin,
            )
        )
        self._plugin_objects[plugin.servicename] = plugin_object

    def _create_services(self):
        for svc in self.get_services():
            svc.log_debug('Creating Service')
            svc.create_all()

    def _subscribe_services(self):
        for svc in self.get_services():
            svc.log_debug('Subscribing Service')
            svc.subscribe_all()

    def _pre_start_services(self):
        for svc in self.get_services():
            svc.log_debug('Pre Starting Service')
            svc.pre_start()

    def start_services(self):
        for svc in self.get_services():
            svc.log_debug('Starting Service')
            svc.start()

    def get_available_editors(self):
        dirs = self._boss.get_editor_dirs()
        return self._loader.get_all_services(dirs)

    def activate_editor(self, name):
        self.load_editor(name)
        self.editor.create_all()
        self.editor.subscribe_all()
        self.editor.pre_start()

    def start_editor(self):
        self.register_editor(self.editor)
        self.editor.start()

    def load_editor(self, name):
        for editor in self.get_available_editors():
            if editor.servicename == name:
                self.editor = editor(self._boss)
                return self.editor
        raise AttributeError(_('No editor found'))

    def register_editor(self, service):
        self._reg.register_plugin(
            instance=service,
            singletons=(
                service.servicename,
                IEditor,
            ),
            features=(
                IService,
            )
        )

    def stop(self):
        for svc in self.get_services():
            svc.stop()






# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
