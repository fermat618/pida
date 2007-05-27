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

"""The Emacs editor core classes for Pida.

This module and other Pida Emacs related classes are based on preliminary works
by Ali Afshar (see Emacs module in Pida 0.2.2).

The Emacs editor for Pida is also, heavily based on the Vim editor.
"""


import logging
import os
import gobject
import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.commands import CommandsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL
from pida.core.log import build_logger

from pida.ui.views import PidaView

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

# Emacs specific
from pida.utils.emacs.emacsembed import EmacsEmbedWidget
from pida.utils.emacs.emacscom import EmacsClient, EmacsServer, EMACS_SCRIPT


class EditorActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'undo',
            TYPE_NORMAL,
            _('Undo'),
            _('Undo the last editor action'),
            gtk.STOCK_UNDO,
            self.on_undo,
        )

        self.create_action(
            'redo',
            TYPE_NORMAL,
            _('Redo'),
            _('Redo the last editor action'),
            gtk.STOCK_REDO,
            self.on_redo,
        )

        self.create_action(
            'cut',
            TYPE_NORMAL,
            _('Cut'),
            _('Cut the selection in the editor'),
            gtk.STOCK_CUT,
            self.on_cut,
        )

        self.create_action(
            'copy',
            TYPE_NORMAL,
            _('Copy'),
            _('Copy the selection in the editor'),
            gtk.STOCK_COPY,
            self.on_copy,
        )

        self.create_action(
            'paste',
            TYPE_NORMAL,
            _('Paste'),
            _('Paste the clipboard in the editor'),
            gtk.STOCK_PASTE,
            self.on_paste,
        )

        self.create_action(
            'save',
            TYPE_NORMAL,
            _('Save'),
            _('Save the current document'),
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


class EmacsView(PidaView):

    def create_ui(self):
        self._emacs = EmacsEmbedWidget('emacs', self.svc.script_path)
        self.add_main_widget(self._emacs)

    def run(self):
        self._emacs.run()

    def grab_input_focus(self):
        self._emacs.grab_input_focus()


class EmacsCallback(object):
    """Emacs editor callback behaviours.

    Communication with Emacs process is handled by EmacsClient in the pIDA->Emacs
    way, and EmacsServer the other way. On occurence of a message, EmacsServer
    extracts a request name and arguments, and then tries to invoke the matching
    method on the EmacsCallback object.
    
    Callbacks' names are built with the Emacs message names, prefixed with 'cb_'.
    Each callback accepts exactly one argument.
    """

    def __init__(self, svc):
        """Constructor."""
        self._log = logging.getLogger('emacs')
        self._svc = svc
        self._server = EmacsServer(self)

    def connect(self):
        """Establish the link with Emacs."""
        return self._server.connect()

    def cb_pida_pong(self, foo):
        """Emacs response to a ping.

        This message is used to test connection at startup.
        """
        self._log.debug('emacs ready')
        self._svc.emit_editor_started()
        return True

    def cb_window_configuration_change_hook(self, filename):
        """Buffer changed event.

        Actually, this hook is called whenever the window containing the
        buffer changes. So notification can occur only when window is resized
        or split for example.
        """
        self._svc.top_buffer = filename
        current = self._svc.current_document
        if filename and (not current or current.filename != filename):
            self._log.debug('emacs buffer changed "%s"' % filename)
            if os.path.isdir(filename):
                self._svc.boss.cmd('filemanager', 'browse', new_path=filename)
                self._svc.boss.cmd('filemanager', 'present_view')
            else:
                self._svc.boss.cmd('buffer', 'open_file', file_name=filename)
        return True
    
    def cb_kill_buffer_hook(self, filename):
        """Buffer closed event."""
        if filename:
            self._log.debug('emacs buffer killed "%s"' % filename)
            self._svc.remove_file(filename)
            self._svc.boss.get_service('buffer').cmd('close_file', file_name=filename)
        return True

    def cb_find_file_hooks(self, filename):
        """File opened event."""
        # Nothing to do here. The window configuration change hook will
        # provide notification for the new buffer.
        if filename:
            self._log.debug('emacs buffer opened "%s"' % filename)
        return True
    
    def cb_after_save_hook(self, filename):
        """Buffer saved event."""
        self._log.debug('emacs buffer saved "%s"' % filename)
        self._svc.boss.cmd('buffer', 'current_file_saved')
        return True
    
    def cb_kill_emacs_hook(self, foo):
        """Emacs killed event."""
        self._log.debug('emacs killed')
        self._svc.inactivate_client()
        self._svc.boss.stop(force=True)
        return False

# Service class
class Emacs(Service):
    """The Emacs service.

    This service is the Emacs editor driver. Emacs instance creation is decided
    there and orders for Emacs are sent to it which forwards them to the
    EmacsClient instance. 
    """ 

    commands_config = EditorCommandsConfig
    actions_config = EditorActionsConfig

    def _create_initscript(self):
        self.script_path = os.path.join(
            self.boss.get_pida_home(), 'pida_emacs_init.el')
        f = open(self.script_path, 'w')
        f.write(EMACS_SCRIPT)
        f.close()

    def emit_editor_started(self):
        self.boss.get_service('editor').emit('started')

    def pre_start(self):
        """Start the editor"""
        self._log = build_logger('emacs')
        self._create_initscript()
        self._documents = {}

        # The current document. Its value is set by Pida and used to drop
        # useless messages to emacs.
        self._current = None

        # The current buffer displayed. Its value is set by the EmacsCallback
        # instance and is used as well to prevent sending useless messages.
        self._top_buffer = ''

        self._current_line = 1
        self._cb = EmacsCallback(self)
        self._client = EmacsClient()
        self._view = EmacsView(self)

        # Add the view to the top level window. Only after that, it will be
        # possible to add a socket in the view.
        self.boss.cmd('window', 'add_view', paned='Editor', view=self._view)

        # Now create the socket and embed the Emacs window.
        self._view.run()
        if self._cb.connect():
            gobject.timeout_add(250, self._client.ping)

    def stop(self):
        self._client.quit()

    def _get_current_document(self):
        return self._current

    def _set_current_document(self, document):
        self._current = document

    current_document = property(fget=_get_current_document,
                                fset=_set_current_document,
                                fdel=None,
                                doc="The document currently edited")

    def _get_top_buffer(self):
        return self._top_buffer

    def _set_top_buffer(self, filename):
        self._top_buffer = filename

    top_buffer = property(fget=_get_top_buffer,
                          fset=_set_top_buffer,
                          fdel=None,
                          doc="The last buffer reported as being viewed by emacs")

    def inactivate_client(self):
        self._client.inactivate()

    def open(self, document):
        """Open a document"""
        if document is not self._current:
            if self.top_buffer != document.filename:
                if document.unique_id in self._documents:
                    self._client.change_buffer(document.filename)
                else:
                    self._client.open_file(document.filename)
                    self._documents[document.unique_id] = document
            self.current_document = document

    def open_many(documents):
        """Open a few documents"""
        pass
    
    def close(self, document):
        if document.unique_id in self._documents:
            self._remove_document(document)
            self._client.close_buffer(document.filename)

    def remove_file(self, filename):
        document = self._get_document_for_filename(filename)
        if document is not None:
            self._remove_document(document)

    def _remove_document(self, document):
        del self._documents[document.unique_id]

    def _get_document_for_filename(self, filename):
        for uid, doc in self._documents.iteritems():
            if doc.filename == filename:
                return doc
            
    def close_all(self):
        """Close all the documents"""

    def save(self):
        """Save the current document"""
        self._client.save_buffer()

    def save_as(self, filename):
        """Save the current document as another filename"""
        pass # TODO

    def revert(self):
        """Revert to the loaded version of the file"""
        self._client.revert_buffer()

    def goto_line(self, line):
        """Goto a line"""
        self._client.goto_line(line + 1)
        self.grab_focus()

    def cut(self):
        """Cut to the clipboard"""
        self._client.cut()

    def copy(self):
        """Copy to the clipboard"""
        self._client.copy()

    def paste(self):
        """Paste from the clipboard"""
        self._client.paste()

    def undo(self):
        self._client.undo()

    def redo(self):
        self._client.redo()

    def grab_focus(self):
        """Grab the focus"""
        self._view.grab_input_focus()

    def define_sign_type(self, name, icon, linehl, text, texthl):
        # TODO
        pass
    
    def undefine_sign_type(self, name):
        # TODO
        pass
    
    #def _add_sign(self, type, filename, line):
        
    #def _del_sign(self, type, filename, line):

    def show_sign(self, type, filename, line):
        # TODO
        pass
    
    def hide_sign(self, type, filename, line):
        # TODO
        pass
    
    def set_current_line(self, line_number):
        self._current_line = line_number

    def get_current_line(self):
        return self._current_line

    #def call_with_current_word(self, callback):
    #   return self._com.get_cword(self.server, callback)

    #def call_with_selection(self, callback):
    #   return self._com.get_selection(self.server, callback)

    def set_path(self, path):
        return self._client.set_directory(path)        


# Required Service attribute for service loading
Service = Emacs


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
