# -*- coding: utf-8 -*- 
"""
    Feature Configs
    ~~~~~~~~~~~~~~~

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from pida.core.base import SubscriberConfig

class FeaturesConfig(SubscriberConfig):
    foreign_name = "features"

    def __init__(self, service):
        SubscriberConfig.__init__(self, service, strict=False)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
