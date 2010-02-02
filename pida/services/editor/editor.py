# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, choices

# locale
from pida.core.locale import Locale
locale = Locale('editor')
_ = locale.gettext

class EditorOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'editor_type',
            _('Editor Type'),
            choices(['vim', 'emacs', 'mooedit']),
            'vim',
            _('The Editor used'),
        )

class EditorEvents(EventsConfig):

    def create(self):
        self.publish('started', 'document-exception', 
            'marker-changed')


# Service class
class Editor(Service):

    """Describe your Service Here""" 

    options_config = EditorOptionsConfig
    events_config = EditorEvents

# Required Service attribute for service loading
Service = Editor



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
