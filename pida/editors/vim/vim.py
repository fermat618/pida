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

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView

from pida.utils.vim.vimembed import VimEmbedWidget
from pida.utils.vim.vimcom import VimCom, VIMSCRIPT

class EditorActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'undo',
            TYPE_NORMAL,
            'Undo',
            'Undo the last editor action',
            gtk.STOCK_UNDO,
        )

        self.create_action(
            'redo',
            TYPE_NORMAL,
            'Redo',
            'Redo the last editor action',
            gtk.STOCK_REDO,
        )

        self.create_action(
            'cut',
            TYPE_NORMAL,
            'Cut',
            'Cut the selection in the editor',
            gtk.STOCK_CUT
        )

        self.create_action(
            'copy',
            TYPE_NORMAL,
            'Copy',
            'Copy the selection in the editor',
            gtk.STOCK_COPY
        )

        self.create_action(
            'paste',
            TYPE_NORMAL,
            'Paste',
            'Paste the clipboard in the editor',
            gtk.STOCK_PASTE
        )

        self.create_action(
            'save',
            TYPE_NORMAL,
            'Save',
            'Save the current document',
            gtk.STOCK_SAVE,
        )


class EditorCommandsConfig(CommandsConfig):

    def open(self, document):
        self.svc.open(document)

    def close(self, document):
        self.svc.close(document)

    def goto_line(self, line):
        self.svc.goto_line(line)

class VimView(PidaView):

    def create_ui(self):
        self._vim = VimEmbedWidget()
        self.add_main_widget(self._vim)

    def run(self):
        self._vim.run()

    def get_server_name(self):
        return self._vim.get_server_name()

    def grab_input_focus(self):
        self._vim.grab_input_focus()



class VimCallback(object):

    def __init__(self, svc):
        self.svc = svc

    def vim_new_serverlist(self, servers):
        if self.svc.server in servers:
            self.svc.init_vim_server()

    def vim_bufferchange(self, server, cwd, file_name, bufnum):
        if file_name:
            if os.path.abspath(file_name) != file_name:
                file_name = os.path.join(cwd, file_name)
            self.svc.boss.get_service('buffer').cmd('open_file', file_name=file_name)

    def vim_bufferunload(self, server, file_name):
        if file_name:
            self.svc.remove_file(file_name)
            self.svc.boss.get_service('buffer').cmd('close_file', file_name=file_name)

    def vim_filesave(self, server, file_name):
        self.svc.boss.cmd('buffer', 'current_file_saved')


# Service class
class Vim(Service):
    """Describe your Service Here""" 

    commands_config = EditorCommandsConfig
    actions_config = EditorActionsConfig

    ##### Vim Things

    def _create_initscript(self):
        script_path = os.path.join(self.boss.get_pida_home(), 'pida_vim_init.vim')
        if not os.path.exists(script_path):
            f = open(script_path, 'w')
            f.write(VIMSCRIPT)
            f.close()

    def init_vim_server(self):
        if self.started == False:
            self._com.stop_fetching_serverlist()
            self._com.load_script(self.server,
                os.path.join(self.boss.get_pida_home(), 'pida_vim_init.vim'))
            self.started = True

    def get_server_name(self):
        return self._view.get_server_name()

    server = property(get_server_name)

    def start(self):
        """Start the editor"""
        self.started = False
        self._cb = VimCallback(self)
        self._com = VimCom(self._cb)
        self._view = VimView(self)
        self.boss.add_view('Editor', self._view)
        self._create_initscript()
        self._newdocs = {}
        self._documents = {}
        self._current = None
        self._view.run()

    def started():
        """Called when the editor has started"""

    def get_current():
        """Get the current document"""

    def open(self, document):
        """Open a document"""
        if not self.started: return
        if document is not self._current:
            if document.unique_id in self._documents:
                if document.unique_id in self._newdocs:
                    fn = self._newdocs[document.unique_id]
                else:
                    fn = document.filename
                self._com.change_buffer(self.server, fn)
                self._com.foreground(self.server)
            else:
                found = False
                #for server in self.__servers:
                #    serverdocs = self.__servers[server]
                #    if document.unique_id in serverdocs:
                #        self.__cw.change_buffer(server, document.filename)
                #        self.__cw.foreground(server)
                #        found = True
                #        break
                if not found:
                    if document.filename is None:
                        newname = self._com.new_file(self.server)
                        self._newdocs[document.unique_id] = newname
                    else:
                        self._com.open_file(self.server, document.filename)
                    self._documents[document.unique_id] = document
            self._current = document

        #if self.single_view is not None:
        #    self.single_view.raise_page()
        #    if document.filename is None:
        #        title = 'New File'
        #    else:
        #        title = document.filename
        #    self.single_view.long_title = title

    def open_many(documents):
        """Open a few documents"""

    def close(self, document):
        if document.unique_id in self._documents:
            self._remove_document(document)
            self._com.close_buffer(self.server, document.filename)

    def remove_file(self, file_name):
        document = self._get_document_for_filename(file_name)
        if document is not None:
            self._remove_document(document)

    def _remove_document(self, document):
        del self._documents[document.unique_id]

    def _get_document_for_filename(self, file_name):
        for uid, doc in self._documents.iteritems():
            if doc.filename == file_name:
                return doc
     

    def close_all():
        """Close all the documents"""

    def save():
        """Save the current document"""

    def save_as(filename):
        """Save the current document as another filename"""

    def revert():
        """Revert to the loaded version of the file"""

    def goto_line(self, line):
        """Goto a line"""
        self._com.goto_line(self.server, line)
        self.grab_focus()

    def cut():
        """Cut to the clipboard"""

    def copy():
        """Copy to the clipboard"""

    def paste():
        """Paste from the clipboard"""

    def grab_focus(self):
        """Grab the focus"""
        self._view.grab_input_focus()

    def set_undo_sensitive(sensitive):
        """Set the undo action sensitivity"""

    def set_redo_sensitive(sensitive):
        """Set the redo action sensitivity"""

    def set_save_sensitive(sensitive):
        """Set the save action sensitivity"""

    def set_revert_sensitive(sensitive):
        """Set the revert sensitivity"""


# Required Service attribute for service loading
Service = Vim



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
