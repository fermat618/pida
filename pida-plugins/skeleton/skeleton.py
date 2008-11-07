# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# stdlib
import sys, compiler, os.path, keyword, re

# gtk
import gtk

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig

# locale
from pida.core.locale import Locale
locale = Locale('skeleton')
_ = locale.gettext

class SkeletonEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                    self.on_document_changed)

    def on_document_changed(self, document):
        pass


class SkeletonFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        pass


class SkeletonOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'Skeleton_for_executing',
            _('Skeleton Executable for executing'),
            str,
            'Skeleton',
            _('The Skeleton executable when executing a module'),
        )


class SkeletonActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'execute_Skeleton',
            TYPE_NORMAL,
            _('Execute Skeleton Module'),
            _('Execute the current Skeleton module in a shell'),
            gtk.STOCK_EXECUTE,
            self.on_Skeleton_execute,
        )

    def on_Skeleton_execute(self, action):
        #self.svc.execute_current_document()
        pass



class Skeleton(LanguageService):

    features_config = SkeletonFeaturesConfig
    actions_config = SkeletonActionsConfig
    options_config = SkeletonOptionsConfig
    events_config = SkeletonEventsConfig

    def pre_start(self):
        pass

    def start(self):
        pass
        
    def stop(self):
        pass


# Required Service attribute for service loading
Service = Skeleton



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
