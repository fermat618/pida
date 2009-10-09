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

# PIDA Imports
import pida.core.environment as env

from pida.ui.views import PidaView

from pida.core.log import get_logger
from pida.core.editors import EditorService 

# Emacs specific
from .emacsembed import EmacsEmbedWidget
from .emacscom import EmacsClient

from pida.core.pdbus import DbusConfig, EXPORT

EEXPORT = EXPORT(suffix='emacs')

class EmacsView(PidaView):
    """
    UI class for emacs editor 
    uses EmacsEmbedWidget to integrate into a PidaView widget
    """
    def create_ui(self):
        self._emacs = EmacsEmbedWidget(
            'emacs',
            self.svc.initscript,
             ['-eval', '(pida-connect 1001)']
        )
        self.add_main_widget(self._emacs)

    def run(self):
        self._emacs.run()

    def grab_input_focus(self):
        self._emacs.grab_input_focus()


class EmacsCallback(object):
    """Emacs editor callback behaviours.

    Communication is done over dbus 
    """

    def __init__(self, svc):
        """Constructor."""
        self._log = get_logger('emacs')
        self._svc = svc

    def em_BufferOpen(self, filename):
        """File opened event."""
        if filename:
            self._log.debug('emacs buffer opened "%s"' % filename)
            self._svc.boss.cmd('buffer', 'open_file', file_name=filename)
        return True

    def em_BufferChange(self, filename):
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
                    self._svc.boss.cmd('filemanager', 'browse', 
                                       new_path=filename)
                    self._svc.boss.cmd('filemanager', 'present_view')
                else:
                    self._svc.boss.cmd('buffer', 'open_file', 
                                       file_name=filename)
        except IOError:
            pass
        return True


    def em_BufferClose(self, filename):
        """Buffer closed event."""
        if filename:
            self._log.debug('emacs buffer killed "%s"' % filename)
            self._svc.remove_file(filename)
            self._svc.boss.cmd('buffer', 'close_file', file_name=filename)
        return True

    def em_BufferSave(self, filename):
        """Buffer saved event."""
        self._log.debug('emacs buffer saved "%s"' % filename)
        self._svc.boss.cmd('buffer', 'current_file_saved')
        return True

    def em_EmacsKill(self):
        """Emacs killed event."""
        self._log.debug('emacs killed')
        self._svc.inactivate_client()
        self._svc.boss.stop(force=True)
        return False

class EmacsDbusConfig(DbusConfig):
    

    @EEXPORT(out_signature = '', in_signature = '')
    def EmacsEnter(self):
        """
        This method is called by emacs to notify emacs is started.
        """
        self.svc.emit_editor_started()

class Emacs(EditorService):
    """The Emacs service.
    This service is the Emacs editor driver. 
    """ 
    dbus_config = EmacsDbusConfig

    def _create_initscript(self):
        return env.get_data_path('pida_emacs_dbus.el')

    def emit_editor_started(self):
        """called when emacs started: Let notify the other services 
        and connect to dbus signals
        """
        self._cb = EmacsCallback(self)
        self._client = EmacsClient(self._cb, self)
        self._client.connect_signals()
        self.boss.get_service('editor').emit('started')
        
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

        #Start Emacs view
        self.initscript = self._create_initscript()
        self._view = EmacsView(self)
        self.boss.window.add_view(paned='Editor', view=self._view)
        self._view.run()


    def stop(self):
        try:
            self._client.quit()
        except AttributeError:
            # gets stopped before the client can register
            pass

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
                          doc="Last buffer reported as being viewed by emacs")

    def inactivate_client(self):
        pass

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

    def open_many(self, documents):
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
    
    def show_sign(self, sign_type, filename, line):
        # TODO
        pass
    
    def hide_sign(self, sign_type, filename, line):
        # TODO
        pass
    
    def set_current_line(self, line_number):
        self._current_line = line_number

    def get_current_line(self):
        return self._current_line

    def set_path(self, path):
        return self._client.set_directory(path)

    @classmethod
    def get_sanity_errors(cls):
        errors = []
        from pida.core.pdbus import has_dbus
        if not has_dbus:
            errors = [
                'dbus python disfunctional',
                'please repair the python dbus bindings',
                '(note that it won\'t work for root)'
            ]

        try:
            import subprocess
            p = subprocess.Popen(
                    ['emacs', '--version'],
                    stdout=subprocess.PIPE,
                    )
            data, _ = p.communicate()
        except OSError:
            errors.extend([
                'emacs not found',
                'please install emacs23 with python support'
            ])
        return errors


# Required Service attribute for service loading
Service = Emacs


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
