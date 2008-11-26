# -*- coding: utf-8 -*- 

"""
    The Emacs editor core classes for Pida
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module and other Pida Emacs related classes
    are based on preliminary worksby Ali Afshar
    (see Emacs module in Pida 0.2.2).

    The Emacs editor for Pida is also,
    heavily based on the Vim editor.

    :copyright: 2007-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""


import logging
import os
import time

# PIDA Imports
import pida.core.environment as env

from pida.ui.views import PidaView

from pida.core.log import get_logger
from pida.core.editors import EditorService, _

# Emacs specific
from pida.utils.emacs.emacsembed import EmacsEmbedWidget
from pida.utils.emacs.emacscom import EmacsClient, EmacsServer
from pida.utils.emacs import emacscom



class EmacsView(PidaView):

    def __init__(self, service, script_path, instance_id, listen_port):
        self._script_path = script_path
        self._instance_id = instance_id
        self._listen_port = listen_port
        PidaView.__init__(self, service)
        
    def create_ui(self):
        self._emacs = EmacsEmbedWidget(
            'emacs',
            self._script_path,
            ['-eval', '(setq server-name "' + self._instance_id + '")', 
             '-eval', '(pida-connect ' + str(self._listen_port) + ')']
        )
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
        self._log = get_logger('emacs')
        self._svc = svc
        self._server = EmacsServer(self)

    def bind(self):
        """Bind the listening socket and return the elected port."""
        return self._server.bind()

    def cb_pida_ping(self, foo):
        """Emacs message to signal it is up and ready.
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
        try:
            if filename and (not current or current.filename != filename):
                self._log.debug('emacs buffer changed "%s"' % filename)
                if os.path.isdir(filename):
                    self._svc.boss.cmd('filemanager', 'browse', new_path=filename)
                    self._svc.boss.cmd('filemanager', 'present_view')
                else:
                    self._svc.boss.cmd('buffer', 'open_file', file_name=filename)
        except IOError:
            pass
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
class Emacs(EditorService):
    """The Emacs service.

    This service is the Emacs editor driver. Emacs instance creation is decided
    there and orders for Emacs are sent to it which forwards them to the
    EmacsClient instance. 
    """ 

    def _create_initscript(self):
        # This method does not create the script anymore but only
        # returns the path of the new script.
        return env.get_data_path('pida_emacs_init.el')

    def emit_editor_started(self):
        self.boss.get_service('editor').emit('started')
        # At this point calling (pida-frame-setup nil) should work, so let's
        # do it.
        self._client.frame_setup()
        
    def pre_start(self):
        """Start the editor"""
        self._documents = {}

        # The current document. Its value is set by Pida and used to drop
        # useless messages to emacs.
        self._current = None

        # The current buffer displayed. Its value is set by the EmacsCallback
        # instance and is used as well to prevent sending useless messages.
        self._top_buffer = ''

        self._current_line = 1

        # Prepare logger for emacs related stuff.
        format = logging.Formatter('%(levelname)s %(name)s: %(message)s')
        emacs_logger = get_logger('emacs')
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        emacs_logger.addHandler(handler)
        if env.is_debug():
            emacs_logger.setLevel(logging.DEBUG)
        else:
            emacs_logger.setLevel(logging.INFO)

        # Start Emacs server.
        self._cb = EmacsCallback(self)

        listen_port = self._cb.bind()
        instance_id = 'pida-' + str(os.getpid())
        self._client = EmacsClient(instance_id, self)

        time.sleep(1)
        self._view = EmacsView(
            self, self._create_initscript(), instance_id, listen_port)

        # Add the view to the top level window. Only after that, it will be
        # possible to add a socket in the view.
        self.boss.cmd('window', 'add_view', paned='Editor', view=self._view)

        # Now create the socket and embed the Emacs window.
        self._view.run()

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
        return True

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
        self._client.goto_line(line)
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
