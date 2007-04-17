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

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView, PidaView

from pida.utils.web import fetch_url


class Bin(object):

    PASTE_URL = None

    def __init__(self, svc):
        self.svc = svc

    def create_data_dict(self, title, name, content, syntax):
        """Override in individual pastebins"""

    def post(self, *args):
        fetch_url(self.PASTE_URL, self.on_posted, self.create_data_dict(*args))

    def on_posted(self, url, content):
        print url

class Dpaste(Bin):

    PASTE_URL = 'http://dpaste.com/'

    def create_data_dict(self, title, name, content, syntax):
        return dict(
            poster = name,
            title = title,
            content = content,
            language = syntax,
        )

class PastebinEditorView(PidaGladeView):

    gladefile = 'paste-editor'

    def on_post_button__clicked(self, button):
        dp = Dpaste(None)
        dp.post(*self.read_values())

    def read_values(self):
        return (self.paste_title.get_text(),
                self.paste_name.get_text(),
                self.paste_content.get_buffer().get_text(
                    self.paste_content.get_buffer().get_start_iter(),
                    self.paste_content.get_buffer().get_end_iter(),
                ),
                'Python',
        )


class PastebinActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'new_paste',
            TYPE_NORMAL,
            'Upload Text Snippet',
            'Upload a text snippet to a pastebin',
            gtk.STOCK_PASTE,
            self.on_new_paste,
        )

    def on_new_paste(self, action):
        self.svc.new_paste()

# Service class
class Pastebin(Service):
    """Describe your Service Here""" 

    actions_config = PastebinActionsConfig

    def new_paste(self):
        editor = PastebinEditorView(self)
        self.boss.cmd('window', 'add_detached_view', paned='Terminal',
                      view=editor)

# Required Service attribute for service loading
Service = Pastebin



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
