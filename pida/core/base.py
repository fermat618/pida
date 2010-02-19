# -*- coding: utf-8 -*-
"""
    Service Configurators
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)


    These "Configs" are not quite configurations,
    but more entities that cause a service to behave in a certain way.
    They provide a way in which an arbitrary number
    of behaviours may be added to a service.

    Each behaviour "publishes" a number of "subscription points"
    which can then be connected to by other services.

    For examples of their use, you can see pida.core.features.

"""

class BaseConfig(object):

    def __init__(self, service):
        self.svc = service
        self.create()

    def create(self):
        """Override to do the creations"""



class SimpleMap(dict):
    """
    simple data mapping for use in SubscriberConfig

    .. warning::
        double subscriptions are destructive
    """

    def add(self, name, instance):
        self[name] = instance

class SubscriberConfig(BaseConfig):
    """
    warning
        double subscriptions are ignored
        double unsubscriptions are breaking stuff
    """

    foreign_name = None

    def __init__(self, service):
        self.published = {}
        self.foreign_subscriptions = []
        BaseConfig.__init__(self, service)

    def publish(self, *points):
        """publish new subscription points

        using the default collection type of set
        """
        self.publish_special(set, *points)

    def publish_special(self, collection, *points):
        """publish new subscription points

        using custom a collection types

        :param collection: the collection type
        """
        for point in points:
            self.published[point] = collection()

    def subscribe(self, point, *data):
        """subscribe `data` to a subscription `point`
        ignores double subscriptions

        note
            for the default implementation using set,
            something will have only one element

            things like language features with special subscription collections may use more elements


        if `name` is not published raise a KeyError
        """
        self.published[point].add(*data)

    def unsubscribe(self, point, *data):
        """unsubscribe an `instance` to the subscription point `name`

        raises `KeyError` if
                  `name` is not published
           or `instance` is not subscribed to `name`
        """
        self.published[point].remove(*data)

    def _get_foreign_config(self, service):
        """internal method to retrieve the config of another service"""
        if not self.foreign_name:
            raise TypeError(
                    "%s cant use foreign configs, "
                    "please set its foreign_name" % self.__class__.__name__)
        service = self.svc.boss.get_service(service)
        return getattr(service, self.foreign_name)

    def subscribe_all_foreign(self):
        """Subscribe to foreign items here"""

    def subscribe_foreign(self, service, point, *data):
        foreign = self._get_foreign_config(service)
        foreign.subscribe(point, *data)
        self.foreign_subscriptions.append((service, point, data))

    def unsubscribe_foreign(self):
        for service, point, data in self.foreign_subscriptions:

            foreign = self._get_foreign_config(service)

            try:
                foreign.unsubscribe(point, *data)
            except KeyError: # ignore unsubscribe errors
                pass

        self.foreign_subscriptions = []


    def has_foreign(self, service, point):
        #XXX: O(N) sucks, but the N shouldn't be that high
        return any(fservice == service and fpoint == point
                   for fservice, fpoint, i in self.foreign_subscriptions)

    def __getitem__(self, point):
        return self.published[point]

    def __iter__(self):
        return iter(self.published)
