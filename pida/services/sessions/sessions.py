# -*- coding: utf-8 -*- 
"""
    Sessions Service
    ~~~~~~~~~~~~~~~~

    currently this saves the open files to a gconf list

    .. todo::
        * window/sudebar/paned positions

    :license: GPL2 or later
    :copyright: 2005-2008 by The PIDA Project
"""

import gobject

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, manager
from pida.core.pdbus import DbusConfig, EXPORT

# locale
from pida.core.locale import Locale
locale = Locale('sessions')
_ = locale.gettext

LEXPORT = EXPORT(suffix='session')

class SessionsOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'load_last_files',
            _('Load last opened files on startup'),
            bool,
            True,
            _('Load last opened files on startup'),
            workspace=True
        )

        self.create_option(
            'open_files',
            _('Open Files'),
            list,
            [],
            _('The list of open files'),
            safe=False,
            workspace=True
            )

    gladefile = 'sessions-properties'
    label_text = _('Sessions Properties')
    icon_name = 'package_utilities'

class SessionsEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):    
        self.subscribe_foreign('buffer', 'document-closed', self.svc.save_files)
        self.subscribe_foreign('buffer', 'document-changed', self.svc.save_files)
        self.subscribe_foreign('editor', 'started', self.svc.load_files)
        self.subscribe_foreign('editor', 'document-exception', self.svc.on_document_exception)

class SessionsDbus(DbusConfig):

    @LEXPORT(out_signature='s')
    def get_session_name(self):
        return manager.session

class Sessions(Service):
    """
    Store opened buffers for later use.
    """
    options_config = SessionsOptionsConfig
    events_config = SessionsEventsConfig
    dbus_config = SessionsDbus

    def load_files(self):
        if self.opt('load_last_files'):
            self.load_buffers(self.opt('open_files'))

    def save_files(self, document=None):
        documents = self.boss.cmd('buffer', 'get_documents')
        files = [d.filename for d in documents.values() if d.filename]
        self.set_opt('open_files', files)

    def load_buffers(self, files):
        """
        load each file in into the buffer manager
        """
        if files:
            self.boss.cmd('buffer', 'open_files', files=files)
    
    def on_document_exception(self, error):
        if error.document.filename in self.opt('open_files'):
            nv = self.opt('open_files')
            nv.remove(error.document.filename)
            self.set_opt('open_files', nv)

Service = Sessions


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
