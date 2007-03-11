import os, imp


class ServiceLoader(object):

    def get_all_services(self, service_dirs):
        for service_path in self._find_all_service_paths(service_dirs):
            module = self._load_service_module(service_path)
            service_class = self._load_service_class(module)
            service_class.servicename = module.servicename
            service_class.servicefile_path = module.servicefile_path
            yield service_class

    def load_all_services(self, service_dirs, boss):
        for service_class in self.get_all_services(service_dirs):
            yield service_class(boss)

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
        fp, pathname, description = imp.find_module(name, [service_path])
        module = imp.load_module(name, fp, pathname, description)
        module.servicename = name
        module.servicefile_path = self._get_servicefile_path(service_path)
        return module

    def _load_service_class(self, module):
        try:
            service = module.Service
        except TypeError, e:
            raise
        except AttributeError, e:
            raise
        service.servicemodule = module
        return service


class ServiceManager(object):

    def __init__(self, boss):
        self._boss = boss
        self._loader = ServiceLoader()

    def load_services(self):
        for svc in self._loader.load_all_services(
                self._boss.service_dirs, self._boss):
            self._boss.register_service(svc)

import sys
sys.path.insert(0, os.getcwd())
from boss import Boss
from pida.core.interfaces import IService
b = Boss(None)
sm = ServiceManager(b)
sm.load_services()
print b._reg.get_singleton('testervice')
print [i for i in b._reg.get_features(IService)]
print b._reg.features
print b._reg.features[IService]
print IService
print b._reg.singletons


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
