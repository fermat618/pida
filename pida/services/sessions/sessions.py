# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import os
import gobject

from pida.utils.configobj import ConfigObj
from tempfile import mkstemp

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, \
    TYPE_TOGGLE
from pida.core.options import OptionsConfig

from pida.core.environment import pida_home

from pida.ui.views import PidaGladeView

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
        files = [d.filename for d in documents.values()]
        self.set_opt('open_files', files)

    def load_buffers(self, files):
        """
        load each file in into the buffer manager
        """
        if files:
            self.boss.cmd('buffer', 'open_file', file_name=files.pop())
        else:
            return
        gobject.timeout_add(1000, self.load_buffers, files)

Service = Sessions


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
