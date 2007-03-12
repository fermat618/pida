
class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create()

    def create(self):
        """Override to do the creations"""

    def get_service_name(self):
        return self.svc.get_name()


