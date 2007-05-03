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




# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig, otype_string_options_factory
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

# locale
from pida.core.locale import Locale
locale = Locale('editor')
_ = locale.gettext

class EditorOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'editor_type',
            _('Editor Type'),
            otype_string_options_factory(['vim']),
            'vim',
            _('The Editor used'),
        )

class EditorEvents(EventsConfig):

    def create_events(self):
        self.create_event('started')


# Service class
class Editor(Service):

    """Describe your Service Here""" 

    options_config = EditorOptionsConfig
    events_config = EditorEvents

# Required Service attribute for service loading
Service = Editor



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
