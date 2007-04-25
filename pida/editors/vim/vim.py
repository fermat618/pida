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
            self.on_undo,
        )

        self.create_action(
            'redo',
            TYPE_NORMAL,
            'Redo',
            'Redo the last editor action',
            gtk.STOCK_REDO,
            self.on_redo,
        )

        self.create_action(
            'cut',
            TYPE_NORMAL,
            'Cut',
            'Cut the selection in the editor',
            gtk.STOCK_CUT,
            self.on_cut,
        )

        self.create_action(
            'copy',
            TYPE_NORMAL,
            'Copy',
            'Copy the selection in the editor',
            gtk.STOCK_COPY,
            self.on_copy,
        )

        self.create_action(
            'paste',
            TYPE_NORMAL,
            'Paste',
            'Paste the clipboard in the editor',
            gtk.STOCK_PASTE,
            self.on_paste,
        )

        self.create_action(
            'save',
            TYPE_NORMAL,
            'Save',
            'Save the current document',
            gtk.STOCK_SAVE,
            self.on_save,
        )

    def on_undo(self, action):
        self.svc.undo()

    def on_redo(self, action):
        self.svc.redo()

    def on_cut(self, action):
        self.svc.cut()

    def on_copy(self, action):
        self.svc.copy()

    def on_paste(self, action):
        self.svc.paste()

    def on_save(self, action):
        self.svc.save()

class EditorCommandsConfig(CommandsConfig):

    def open(self, document):
        self.svc.open(document)

    def close(self, document):
        self.svc.close(document)

    def goto_line(self, line):
        self.svc.goto_line(line)

    def define_sign_type(self, type, icon, linehl, text, texthl):
        self.svc.define_sign_type(type, icon, linehl, text, texthl)

    def undefine_sign_type(self, type):
        self.svc.undefine_sign_type(type)

    def get_current_line_number(self):
        return self.svc.get_current_line()

    def show_sign(self, type, file_name, line):
        self.svc.show_sign(type, file_name, line)

    def hide_sign(self, type, file_name, line):
        self.svc.hide_sign(type, file_name, line)

    def call_with_current_word(self, callback):
        self.svc.call_with_current_word(callback)

    def call_with_selection(self, callback):
        self.svc.call_with_selection(callback)

    def grab_focus(self):
        self.svc.grab_focus()


class VimView(PidaView):

    def create_ui(self):
        self._vim = VimEmbedWidget('gvim', self.svc.script_path)
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

    def vim_cursor_move(self, server, line_number):
        self.svc.set_current_line(int(line_number))


# Service class
class Vim(Service):
    """Describe your Service Here""" 

    commands_config = EditorCommandsConfig
    actions_config = EditorActionsConfig

    ##### Vim Things

    def _create_initscript(self):
        self.script_path = os.path.join(self.boss.get_pida_home(), 'pida_vim_init.vim')
        f = open(self.script_path, 'w')
        f.write(VIMSCRIPT)
        f.close()

    def init_vim_server(self):
        if self.started == False:
            self._com.stop_fetching_serverlist()
            self.started = True
            self._emit_editor_started()

    def _emit_editor_started(self):
        self.boss.get_service('editor').emit('started')

    def get_server_name(self):
        return self._view.get_server_name()

    server = property(get_server_name)

    def pre_start(self):
        """Start the editor"""
        self.started = False
        self._create_initscript()
        self._cb = VimCallback(self)
        self._com = VimCom(self._cb)
        self._view = VimView(self)
        self.boss.cmd('window', 'add_view', paned='Editor', view=self._view)
        self._documents = {}
        self._current = None
        self._sign_index = 0
        self._signs = {}
        self._current_line = 1
        self._view.run()


    def open(self, document):
        """Open a document"""
        if document is not self._current:
            if document.unique_id in self._documents:
                fn = document.filename
                self._com.change_buffer(self.server, fn)
                self._com.foreground(self.server)
            else:
                self._com.open_file(self.server, document.filename)
                self._documents[document.unique_id] = document
            self._current = document


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

    def save(self):
        """Save the current document"""
        self._com.save(self.server)

    def save_as(filename):
        """Save the current document as another filename"""

    def revert():
        """Revert to the loaded version of the file"""

    def goto_line(self, line):
        """Goto a line"""
        self._com.goto_line(self.server, line)
        self.grab_focus()

    def cut(self):
        """Cut to the clipboard"""
        self._com.cut(self.server)

    def copy(self):
        """Copy to the clipboard"""
        self._com.copy(self.server)

    def paste(self):
        """Paste from the clipboard"""
        self._com.paste(self.server)

    def undo(self):
        self._com.undo(self.server)

    def redo(self):
        self._com.redo(self.server)

    def grab_focus(self):
        """Grab the focus"""
        self._view.grab_input_focus()

    def define_sign_type(self, name, icon, linehl, text, texthl):
        self._com.define_sign(self.server, name, icon, linehl, text, texthl)

    def undefine_sign_type(self, name):
        self._com.undefine_sign(self.server, name)

    def _add_sign(self, type, filename, line):
        self._sign_index += 1
        self._signs[(filename, line, type)] = self._sign_index
        return self._sign_index
        
    def _del_sign(self, type, filename, line):
        try:
            return self._signs.pop((filename, line, type))
        except KeyError:
            self.window.error_dlg('Tried to remove non-existent sign')

    def show_sign(self, type, filename, line):
        index = self._add_sign(type, filename, line)
        self._com.show_sign(self.server, index, type, filename, line)
   
    def hide_sign(self, type, filename, line):
        index = self._del_sign(type, filename, line)
        self._com.hide_sign(self.server, index, filename)
   
    def set_current_line(self, line_number):
        self._current_line = line_number

    def get_current_line(self):
        return self._current_line

    def call_with_current_word(self, callback):
        return self._com.get_cword(self.server, callback)

    def call_with_selection(self, callback):
        return self._com.get_selection(self.server, callback)

# Required Service attribute for service loading
Service = Vim



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
