
class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create()

    def create(self):
        """Override to do the creations"""



class SubscriberConfig(BaseConfig):


    foreign_name = None

    def __init__(self, service):
        self.published = {}
        self.foreign_subscriptions = []
        BaseConfig.__init__(self, service)

    def publish(self, name):
        """publish a new subscription point"""
        self.published[name] = set()

    def subscribe(self, name, instance):
        """subscribe an `instance` to the subscription point `name`
        ignores double subscriptions

        if `name` is not published raise a KeyError
        """
        self.published[name].add(instance)

    def unsubscribe(self, name, instance):
        """unsubscribe an `instance` to the subscription point `name`

        raises `KeyError` if 
                  `name` is not published 
           or `instance` is not subscribed to `name`
        """
        self.published[name].remove(instance)

    def _get_foreign_config(self, service):
        """internal method to retrieve the config of another service"""
        if not self.foreign_name:
            raise TypeError(
                    "%s cant use foreign configs, "
                    "please set its foreign_name"%self.__class__.__name__)
        service = self.svc.boss.get_service(service)
        return getattr(service, self.foreign_name)


    def subscribe_foreign(self, service, name, instance):
        foreign = self._get_foreign_config(service)
        foreign.subscribe(name, instance)
        self.foreign_subscriptions.append((service, name, instance))

    def unsubscribe_foreign(self):
        for service, name, instance in self.foreign_subscriptions:

            foreign = self._get_foreign_config(service)

            try:
                foreign.unsubscribe(name, instance)
            except KeyError: # ignore unsubscribe errors
                pass

        self.foreign_subscriptions.clear()


    def has_foreign(self, service, name):
        #XXX: O(N) sucks, but the N shouldn't be that high
        return any( fservice == service and fname == name 
                    for fservice, fname, i in self.foreign_subscriptions)

    def __getitem__(self, key):
        return self.published[key]

    def __iter__(self):
        return iter(self.published)
