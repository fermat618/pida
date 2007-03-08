
class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create_all()

    def create_all(self):
        """Override to do the creations"""

    def bind_all(self):
        """Override to do the bindings"""

    def get_service_name(self):
        return self.svc.get_name()


