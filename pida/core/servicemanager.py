import os, imp

from pida.core.interfaces import IService, IEditor
from pida.core.plugins import Registry

from pida.core.environment import library, environ


def sort_services_func(s1, s2):
    return cmp(s1.servicename, s2.servicename)

class ServiceLoader(object):

    def get_all_services(self, service_dirs):
        classes = []
        for service_path in self._find_all_service_paths(service_dirs):
            module = self._load_service_module(service_path)
            if module is not None:
                service_class = self._load_service_class(module)
                if service_class is not None:
                    service_class.servicename = module.servicename
                    service_class.servicefile_path = module.servicefile_path
                    classes.append(service_class)
        classes.sort(sort_services_func)
        return classes

    def load_all_services(self, service_dirs, boss):
        services = []
        for service_class in self.get_all_services(service_dirs):
            services.append(service_class(boss))
        services.sort(sort_services_func)
        return services

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
        except ImportError:
            return None
        module = imp.load_module(name, fp, pathname, description)
        module.servicename = name
        module.servicefile_path = self._get_servicefile_path(service_path)
        self._register_service_env(name, service_path)
        return module

    def _load_service_class(self, module):
        try:
            service = module.Service
        except AttributeError, e:
            return None
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
        self._loader = ServiceLoader()
        self._reg = Registry()

    def activate_services(self): 
        self.load_services() 
        self.create_all()
        self.subscribe_all()
        self.pre_start_all()


    def load_services(self):
        for svc in self._loader.load_all_services(
                self._boss.get_service_dirs(), self._boss):
            self.register_service(svc)

    def register_service(self, service):
        self._reg.register_plugin(
            instance=service,
            singletons=(
                service.servicename,
            ),
            features=(
                IService,
            )
        )

    def get_service(self, name):
        return self._reg.get_singleton(name)

    def get_services(self):
        services = list(self._reg.get_features(IService))
        services.sort(sort_services_func)
        return services

    def create_all(self):
        for svc in self.get_services():
            svc.create_all()

    def subscribe_all(self):
        for svc in self.get_services():
            svc.subscribe_all()

    def pre_start_all(self):
        for svc in self.get_services():
            svc.pre_start()

    def start_services(self):
        for svc in self.get_services():
            svc.start()

    def activate_editor(self, name):
        self.load_editor(name)
        self.editor.create_all()
        self.editor.subscribe_all()
        self.editor.pre_start()

    def start_editor(self):
        self.editor.start()

    def load_editor(self, name):
        dirs = self._boss.get_editor_dirs()
        for editor in self._loader.get_all_services(dirs):
            if editor.servicename == name:
                self.editor = editor(self._boss)
                return self.editor
        raise AttributeError('No editor found')

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
