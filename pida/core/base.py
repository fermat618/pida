
class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create()

    def create(self):
        """Override to do the creations"""

