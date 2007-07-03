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
from tempfile import mkstemp

import gtk

from kiwi.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView
from pida.ui.objectlist import AttrSortCombo
from pida.core.document import Document

# locale
from pida.core.locale import Locale
locale = Locale('buffer')
_ = locale.gettext



LIST_COLUMNS = [
    Column('markup', use_markup=True),
    Column("basename", visible=False, searchable=True),
]

class BufferListView(PidaGladeView):

    gladefile = 'buffer_list'
    locale = locale
    icon_name = 'package_office'

    label_text = _('Buffers')

    def create_ui(self):
        self.buffers_ol.set_columns(LIST_COLUMNS)
        self.buffers_ol.set_headers_visible(False)
        self._sort_combo = AttrSortCombo(self.buffers_ol,
            [
                ('creation_time', _('Time Opened')),
                ('filename', _('File path')),
                ('basename', _('File name')),
                ('mimetype', _('Mime Type')),
                ('length', _('File Length')),
                ('modified_time', _('Last Modified')),
                #('Project', _('Project_name'))
            ],
            'creation_time' 
        )
        self._sort_combo.show()
        self.main_vbox.pack_start(self._sort_combo, expand=False)

    def add_document(self, document):
        self.buffers_ol.append(document)

    def remove_document(self, document):
        self.buffers_ol.remove(document)

    def set_document(self, document):
        if self.buffers_ol.get_selected() is not document:
            self.buffers_ol.select(document)

    def on_buffers_ol__selection_changed(self, ol, item):
        self.svc.view_document(item)

    def on_buffers_ol__double_click(self, ol, item):
        self.svc.boss.editor.cmd('grab_focus')

    def on_buffers_ol__right_click(self, ol, item, event=None):
        self.svc.boss.cmd('contexts', 'popup_menu', context='file-menu',
                          event=event,
                          file_name=self.svc.get_current().filename)

    def get_current_buffer_index(self):
        return self.buffers_ol.index(self.buffers_ol.get_selected())

    def select_buffer_by_index(self, index):
        self.buffers_ol.select(self.buffers_ol[index])

    def next_buffer(self):
        index = self.get_current_buffer_index()
        newindex = index + 1
        if newindex == len(self.buffers_ol):
            newindex = 0
        self.select_buffer_by_index(newindex)

    def prev_buffer(self):
        index = self.get_current_buffer_index()
        newindex = index - 1
        if newindex == -1:
            newindex = len(self.buffers_ol) - 1
        self.select_buffer_by_index(newindex)

class BufferActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'open_file',
            TYPE_NORMAL,
            _('Open File'),
            _('Open a file with a graphical file browser'),
            gtk.STOCK_OPEN,
            self.on_open_file,
            '<Shift><Control>O',
        )
        
        self.create_action(
            'open-for-file',
            TYPE_NORMAL,
            _('Open File'),
            _('Open this file'),
            gtk.STOCK_OPEN,
            self.on_open_for_file,
            'NOACCEL',
        )

        self.create_action(
            'new_file',
            TYPE_NORMAL,
            _('New File'),
            _('Create a temporary new file'),
            gtk.STOCK_NEW,
            self.on_new_file,
            '<Shift><Control>N',
        )

        self.create_action(
            'create_file',
            TYPE_NORMAL,
            _('Create File'),
            _('Create a new file'),
            gtk.STOCK_ADD,
            self.on_add_file,
            '<Shift><Control>A',
        )

        self.create_action(
            'close',
            TYPE_NORMAL,
            _('Close Document'),
            _('Close the current document'),
            gtk.STOCK_CLOSE,
            self.on_close,
            '<Shift><Control>W',
        )

        self.create_action(
            'switch_next_buffer',
            TYPE_NORMAL,
            _('Next Buffer'),
            _('Switch to the next buffer'),
            gtk.STOCK_GO_DOWN,
            self.on_next_buffer,
            '<Alt>Down',
        )

        self.create_action(
            'switch_prev_buffer',
            TYPE_NORMAL,
            _('Previous Buffer'),
            _('Switch to the previous buffer'),
            gtk.STOCK_GO_UP,
            self.on_prev_buffer,
            '<Alt>Up',
        )

    def on_open_file(self, action):
        file_name = self.svc.boss.window.open_dlg()
        if file_name:
            self.svc.open_file(file_name)

    def on_new_file(self, action):
        fd, file_name = mkstemp()
        os.close(fd)
        self.svc.open_file(file_name)

    def on_add_file(self, action):
        file_name = self.svc.boss.window.save_dlg()
        if file_name:
            f = open(file_name, 'w')
            f.close()
            self.svc.open_file(file_name)

    def on_close(self, action):
        self.svc.close_current()

    def on_open_for_file(self, action):
        file_name = action.contexts_kw['file_name']
        self.svc.open_file(file_name)

    def on_next_buffer(self, action):
        self.svc.get_view().next_buffer()

    def on_prev_buffer(self, action):
        self.svc.get_view().prev_buffer()


class BufferFeaturesConfig(FeaturesConfig):

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'buffer-file-menu.xml'))

class BufferEventsConfig(EventsConfig):

    def create_events(self):
        self.create_event('document-saved')
        self.create_event('document-changed')

class BufferCommandsConfig(CommandsConfig):

    def open_file(self, file_name):
        self.svc.open_file(file_name)

    def close_file(self, file_name):
        self.svc.close_file(file_name)

    def current_file_saved(self):
        self.svc.file_saved()

    def get_view(self):
        return self.svc.get_view()

    def get_current(self):
        return self.svc.get_current()

    def get_documents(self):
        return self.svc.get_documents()

# Service class
class Buffer(Service):
    """
    Buffer is a graphical manager for vim buffers.
    """ 

    commands_config = BufferCommandsConfig
    actions_config = BufferActionsConfig
    events_config = BufferEventsConfig
    features_config = BufferFeaturesConfig

    def pre_start(self):
        self._documents = {}
        self._current = None
        self._view = BufferListView(self)
        self.get_action('close').set_sensitive(False)
        self._refresh_buffer_action_sensitivities()

    def get_view(self):
        return self._view

    def _refresh_buffer_action_sensitivities(self):
        for action_name in ['switch_next_buffer', 'switch_prev_buffer']:
            self.get_action(action_name).set_sensitive(len(self._documents) > 0)

    def open_file(self, file_name):
        doc = self._get_document_for_filename(file_name)
        if doc is None:
            doc = Document(self.boss, file_name)
            self._add_document(doc)
        self.view_document(doc)

    def close_current(self):
        if self._current is not None:
            self._remove_document(self._current)
            self.boss.editor.cmd('close', document=self._current)

    def close_file(self, file_name):
        document = self._get_document_for_filename(file_name)
        if document is not None:
            self._remove_document(document)
            self.boss.editor.cmd('close', document=document)

    def _get_document_for_filename(self, file_name):
        for uid, doc in self._documents.iteritems():
            if doc.filename == file_name:
                return doc

    def _add_document(self, document):
        self._documents[document.unique_id] = document
        self._view.add_document(document)
        self._refresh_buffer_action_sensitivities()

    def _remove_document(self, document):
        del self._documents[document.unique_id]
        self._view.remove_document(document)
        self._refresh_buffer_action_sensitivities()

    def view_document(self, document):
        if document is not None and self._current is not document:
            self._current = document
            self._view.set_document(document)
            self.boss.editor.cmd('open', document=document)
            self.emit('document-changed', document=document)
        self.get_action('close').set_sensitive(document is not None)

    def file_saved(self):
        self.emit('document-saved', document=self._current)

    def get_current(self):
        return self._current

    def get_documents(self):
        return self._documents


# Required Service attribute for service loading
Service = Buffer



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
