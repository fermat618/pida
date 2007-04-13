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


from kiwi.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView
from pida.core.document import Document

PROJECT_LIST_COLUMNS = [
    Column('markup', use_markup=True)
]

class BufferListView(PidaGladeView):

    gladefile = 'buffer_list'

    icon_name = 'package_office'

    label_text = 'Buffers'

    def create_ui(self):
        self.buffers_ol.set_columns(PROJECT_LIST_COLUMNS)

    def add_document(self, document):
        self.buffers_ol.append(document)

    def set_document(self, document):
        if self.buffers_ol.get_selected() is not document:
            self.buffers_ol.select(document)

    def on_buffers_ol__selection_changed(self, ol, item):
        self.svc.view_document(item)

class BufferCommandsConfig(CommandsConfig):

    def open_file(self, file_name):
        self.svc.open_file(file_name)

# Service class
class Buffer(Service):
    """Describe your Service Here""" 

    commands_config = BufferCommandsConfig

    def start(self):
        self._documents = {}
        self._current = None
        self._view = BufferListView(self)
        self.boss.add_view('Buffer', self._view)

    def open_file(self, file_name):
        doc = self._get_document_for_filename(file_name)
        if doc is None:
            doc = Document(file_name)
            self._add_document(doc)
        self.view_document(doc)

    def _get_document_for_filename(self, file_name):
        for uid, doc in self._documents.iteritems():
            if doc.filename == file_name:
                return doc

    def _add_document(self, document):
        self._documents[document.unique_id] = document
        self._view.add_document(document)

    def view_document(self, document):
        if self._current is not document:
            self._current = document
            self._view.set_document(document)
            self.boss.get_service('vim').cmd('open', document=document)


# Required Service attribute for service loading
Service = Buffer



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
