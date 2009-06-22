# -*- coding: utf-8 -*- 
"""
    pida.editors.vim.vim
    ~~~~~~~~~~~~~~~~~~~~

    :license: GPL 2 or later
    :copyright: 2007-2008 the Pida Project
"""
import os, uuid

# PIDA Imports
from pida.core.environment import get_data_path

from pida.ui.views import PidaView

from .embed import VimEmbedWidget
#from .com import VimCom

from .client import VimCom

from pida.core.editors import EditorService, _

UID = 'PIDA_EMBEDDED_%s' % uuid.uuid4().get_hex()


def _do_nothing(*args):
    pass

nothing_async = dict(reply_handler=_do_nothing,
                error_handler=_do_nothing)

class VimView(PidaView):

    def create_ui(self):
        self._vim = VimEmbedWidget('gvim', self.svc.script_path, UID)
        self.add_main_widget(self._vim)

    def run(self):
        return self._vim.run()

    def get_server_name(self):
        return self._vim.server_name
 
    def grab_input_focus(self):
         self._vim.grab_input_focus()


class VimCallback(object):

    def __init__(self, svc):
        self.svc = svc

    def vim_VimEnter(self):
        self.svc._emit_editor_started()

    def vim_BufEnter(self):
        fn = self.svc._com.get_current_buffer()
        cwd = self.svc._com.get_cwd()
        path = os.path.realpath(os.path.join(cwd, fn))
        self.svc.boss.cmd('buffer', 'open_file', file_name=path)

    def vim_BufDelete(self, file_name):
        if file_name == '':
            return
        self.svc.remove_file(file_name)
        self.svc.boss.get_service('buffer').cmd('close_file', file_name=file_name)

    def vim_VimLeave(self):
        self.svc.boss.stop(force=True)

    def vim_BufWritePost(self):
        self.svc.boss.cmd('buffer', 'current_file_saved')

    def vim_CursorMoved(self):
        pass

    #def vim_new_serverlist(self, servers):
    #    if self.svc.server in servers:
    #        self.svc.init_vim_server()

    #def vim_bufferchange(self, server, cwd, file_name, bufnum):
    #    if server == self.svc.server:
    #        if file_name:
    #            if os.path.abspath(file_name) != file_name:
    #                file_name = os.path.join(cwd, file_name)
    #            if os.path.isdir(file_name):
    #                self.svc.boss.cmd('filemanager', 'browse', new_path=file_name)
    #                self.svc.boss.cmd('filemanager', 'present_view')
    #                self.svc.open_last()
    #            else:
    #                self.svc.boss.cmd('buffer', 'open_file', file_name=file_name)

    def vim_bufferunload(self, server, file_name):
        if server == self.svc.server:
            if file_name:
                self.svc.remove_file(file_name)
                self.svc.boss.get_service('buffer').cmd('close_file', file_name=file_name)

    def vim_filesave(self, server, file_name):
        if server == self.svc.server:
            self.svc.boss.cmd('buffer', 'current_file_saved')

    def vim_cursor_move(self, server, line_number):
        if server == self.svc.server:
            self.svc.set_current_line(int(line_number))

    def vim_shutdown(self, server, args):
        if server == self.svc.server:
            self.svc.boss.stop(force=True)

    def vim_complete(self, server, temp_buffer_filename, offset):
        buffer = open(temp_buffer_filename).read()
        offset = int(offset) - 1
        from rope.ide.codeassist import PythonCodeAssist
        from rope.base.project import Project
        p = Project(self.svc.boss.cmd('buffer', 'get_current').directory)
        c = PythonCodeAssist(p)
        co = c.assist(buffer, offset).completions
        print co
        for comp in co:
            self.svc._com.add_completion(server, comp.name)
        # do this a few times
        #self.svc._com.add_completion(server, 'banana')
        pass


# Service class
class Vim(EditorService):
    """Describe your Service Here""" 

    ##### Vim Things

    def _create_initscript(self):
        self.script_path = get_data_path('pida.vim')

    #def init_vim_server(self):
    #    if self.started == False:
    #        self._com.stop_fetching_serverlist()
    #        self.started = True
    #        self._emit_editor_started()

    def _emit_editor_started(self):
        self.boss.get_service('editor').emit('started')

    #@property
    #def server(self):
    #    return self._view.get_server_name()


    def pre_start(self):
        """Start the editor"""
        self.started = False
        self._create_initscript()
        self._view = VimView(self)
        self.boss.window.add_view(paned='Editor', view=self._view)
        success = self._view.run()
        self._cb = VimCallback(self)
        self._com = VimCom(self._cb, os.environ['PIDA_DBUS_UUID'])
        self._documents = {}
        self._current = None
        self._sign_index = 0
        self._signs = {}
        self._current_line = 1
        if not success:
            err = _( 'There was a problem running the "gvim" '
                     'executable. This is usually because it is not '
                     'installed. Please check that you can run "gvim" '
                     'from the command line.')
            self.error_dlg(err)
            raise RuntimeError(err)


    def open(self, document):
        """Open a document"""


        if document is not self._current:
            fn = document.filename
            if document.unique_id in self._documents:
                self._com.open_buffer(fn, **nothing_async)
            else:
                self._com.open_file(fn, **nothing_async)
                self._documents[document.unique_id] = document
            self._current = document


    def open_many(self, documents):
        """Open a few documents"""
        pass

    def close(self, document):
        if document.unique_id in self._documents:
            self._remove_document(document)
            self._com.close_buffer(document.filename, **nothing_async)
        return True

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
        self._com.save_current_buffer()

    def save_as(self, filename):
        """Save the current document as another filename"""
        self._com.save_as_current_buffer(filename)

    def revert():
        """Revert to the loaded version of the file"""

    def goto_line(self, line):
        """Goto a line"""
        self._com.goto_line(line)
        self.grab_focus()

    def cut(self):
        """Cut to the clipboard"""
        self._com.cut()

    def copy(self):
        """Copy to the clipboard"""
        self._com.copy()

    def paste(self):
        """Paste from the clipboard"""
        self._com.paste()

    def undo(self):
        self._com.undo()

    def redo(self):
        self._com.redo()

    def grab_focus(self):
        """Grab the focus"""
        self._view.grab_input_focus()

    def define_sign_type(self, name, icon, linehl, text, texthl):
        self._com.define_sign(name, icon, linehl, text, texthl)

    def undefine_sign_type(self, name):
        self._com.undefine_sign(name)

    def _add_sign(self, type, filename, line):
        self._sign_index += 1
        self._signs[(filename, line, type)] = self._sign_index
        return self._sign_index
        
    def _del_sign(self, type, filename, line):
            return self._signs.pop((filename, line, type))

    def show_sign(self, type, filename, line):
        index = self._add_sign(type, filename, line)
        self._com.show_sign(index, type, filename, line)
   
    def hide_sign(self, type, filename, line):
        try:
            index = self._del_sign(type, filename, line)
            self._com.hide_sign(index, filename)
        except KeyError:
            self.window.error_dlg(_('Tried to remove non-existent sign'))
   
    def set_current_line(self, line_number):
        self._current_line = line_number

    def get_current_line(self):
        return self._current_line

    def delete_current_word(self):
        self._com.delete_cword(self.server)

    def insert_text(self, text):
        self._com.insert_text(self.server, text)

    def call_with_current_word(self, callback):
        return self._com.get_cword(self.server, callback)

    def call_with_selection(self, callback):
        return self._com.get_selection(self.server, callback)

    def set_path(self, path):
        return self._com.cd(path)

    def get_cursor_offset(self):
        return self._com.get_cursor_offset()

    get_cursor_position = get_cursor_offset

    def set_cursor_offset(self, offset):
        self._com.set_cursor_offset(offset, **nothing_async)

    set_cursor_position = set_cursor_offset

    def stop(self):
        self._com.quit(reply_handler=lambda *a: None,
                       error_handler=lambda *a: None)
        return

    #FIXME list of missing functions

    #def set_content(self, editor, value)
    #def get_content(self, editor)
    
# Required Service attribute for service loading
Service = Vim



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
