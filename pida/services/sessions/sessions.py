# -*- coding: utf-8 -*- 
"""
    Sessions Service
    ~~~~~~~~~~~~~~~~

    currently this saves the open files to a gconf list

    .. todo::
        * window/sudebar/paned positions

    :license: GPL2 or later
    :copyright:
        * 2007 Ali Afshar
        * 2008 Ronny Pfannschmidt
"""

import gobject

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig

# locale
from pida.core.locale import Locale
locale = Locale('sessions')
_ = locale.gettext


class SessionsOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'load_last_session',
            _('Load last session on startup'),
            bool,
            True,
            _('Load last session on startup'),
        )

        self.create_option(
            'clear_old_buffers',
            _('Clear old buffers when loading session'),
            bool,
            False,
            _('Clear old buffers when loading session'),
        )

        self.create_option(
            'open_files',
            _('Open Files'),
            list,
            [],
            _('The list of open files'),
            )

    gladefile = 'sessions-properties'
    label_text = _('Sessions Properties')
    icon_name = 'package_utilities'

class SessionsEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):    
        self.subscribe_foreign('buffer', 'document-changed', self.svc.save_session)
        self.subscribe_foreign('editor', 'started', self.svc.load_session)

class Sessions(Service):
    """
    Store opened buffers for later use.
    """
    options_config = SessionsOptionsConfig
    events_config = SessionsEventsConfig

    def load_session(self):
        if self.opt('load_last_session'):
            self.load_buffers(self.opt('open_files'))

    def save_session(self, document=None):
        documents = self.boss.cmd('buffer', 'get_documents')
        files = [d.filename for d in documents.values() if d.filename]
        self.set_opt('open_files', files)

    def load_buffers(self, files):
        """
        load each file in into the buffer manager
        """
        if files:
            self.boss.cmd('buffer', 'open_file', file_name=files.pop())
        else:
            return
        #XXX: this way is not acceptable,
        #     need find a way to tell editors to open at once
        gobject.timeout_add(1000, self.load_buffers, files)

Service = Sessions


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
