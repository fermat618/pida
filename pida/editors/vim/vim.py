# -*- coding: utf-8 -*- 
"""
    pida.editors.vim.vim
    ~~~~~~~~~~~~~~~~~~~~

    :license: GPL 2 or later
    :copyright: 2007-2008 the Pida Project
"""

import os

from pida.core.environment import get_data_path
from pida.core.editors import EditorService, _
from pida.ui.views import PidaView

from .embed import VimEmbedWidget
from .client import VimCom

_ignore = dict(reply_handler=lambda *a: None,
               error_handler=lambda *a: None)

VIM_LAUNCH_ERR = _('There was a problem running the "gvim" '
                   'executable. This is usually because it is not '
                   'installed. Please check that you can run "gvim" '
                   'from the command line.')


class VimView(PidaView):

    def create_ui(self):
        self._vim = VimEmbedWidget('gvim', self.svc.script_path)
        self.add_main_widget(self._vim)

    def run(self):
        return self._vim.run()

    def get_server_name(self):
        return self._vim.server_name

    def grab_input_focus(self):
         self._vim.grab_input_focus()

def _debug(f):
    def _wrapped(*args, **kw):
        print f.__name__, args, kw
        return f(*args, **kw)
    return _wrapped

class VimCallback(object):

    def __init__(self, svc):
        self.svc = svc


    def connect(self, proxy):
        for k in dir(self):
            if k.startswith('vim_'):
                proxy.connect_to_signal(k[4:], getattr(self, k))

    def vim_VimEnter(self):
        self.svc.boss.get_service('editor').emit('started')

    def vim_BufEnter(self, bufid, filename):
        path = unicode(filename)
        if not path:
            path = None
        elif os.path.isdir(path):
            path = None
        else:
            cwd = self.svc._com.get_cwd()
            path = os.path.realpath(os.path.join(cwd, path))
        bufid = int(bufid)
        self.svc.boss.cmd('buffer', 'open_file', file_name=path,
                           editor_buffer_id=bufid, do_open=False)

    def vim_BufNew(self, bufid):
        pass

    def vim_BufUnload(self, bufid):
        pass

    def vim_BufLeave(self, bufid):
        pass

    def vim_BufWipeout(self, bufid):
        pass

    def vim_BufDelete(self, bufid):
        self.svc.boss.get_service('buffer').cmd('close_file',
                                    editor_buffer_id=int(bufid))

    def vim_BufReadPre(self, bufid):
        pass

    def vim_BufReadPost(self, bufid):
        pass

    def vim_BufWritePre(self, bufid):
        pass

    def vim_BufNewFile(self, bufid):
        pass

    def vim_BufAdd(self, bufid):
        pass

    def vim_VimLeave(self):
        self.svc.boss.stop(force=True)

    def vim_BufWritePost(self, bufid):
        self.svc.boss.cmd('buffer', 'current_file_saved')

    def vim_CursorMoved(self):
        pass


# Service class
class Vim(EditorService):
    """Vim Editor Service
    """
    def __init__(self, *args, **kw):
        EditorService.__init__(self, *args, **kw)
        self._sign_index = 0
        self._signs = {}
        self.script_path = get_data_path('pida.vim')

    def pre_start(self):
        """Start the editor"""
        self._view = VimView(self)
        self.boss.window.add_view(paned='Editor', view=self._view)
        if not self._view.run():
            self.error_dlg(VIM_LAUNCH_ERR)
            raise RuntimeError(err)
        self._cb = VimCallback(self)
        self._com = VimCom(self._cb, os.environ['PIDA_DBUS_UUID'])

    def open(self, document):
        """Open a document"""
        if document.editor_buffer_id is not None:
            self._com.open_buffer_id(document.editor_buffer_id,
                                     **_ignore)
        else:
            def tag_document(document=document):
                document.editor_buffer_id = int(self._com.get_buffer_number(
                    document.filename))

            def tag_new(document=document):
                document.editor_buffer_id = int(self._com.get_current_buffer_id())

            def error(*args):
                pass

            if document.is_new:
                self._com.new_file(reply_handler=tag_new,
                                   error_handler=error)
            else:
                self._com.open_file(document.filename,
                                    reply_handler=tag_document,
                                    error_handler=lambda *a: None)

    def open_many(self, documents):
        """Open a few documents"""
        pass

    def close(self, document):
        print ['vimclose', document, document.editor_buffer_id]
        if document.editor_buffer_id is not None:
            self._com.close_buffer_id(document.editor_buffer_id,
                                      **_ignore)
        return True

    def close_all():
        """Close all the documents"""

    def save(self):
        """Save the current document"""
        name = self._com.get_current_buffer()
        if name:
            self._com.save_current_buffer()
        else:
            self.save_as()

    def save_as(self):
        """Save the current document as another filename"""
        current_folder = self.boss.cmd('filemanager', 'get_browsed_path')
        file_name = self.boss.window.save_dlg(folder=current_folder)
        if file_name:
            document = self.boss.cmd('buffer', 'get_current')
            document.filename = file_name
            self._com.save_as_current_buffer(file_name)
            self.boss.cmd('buffer', 'open_file', document=document)

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

    def get_current_line(self):
        return self._com.get_current_linenumber()

    def delete_current_word(self):
        self._com.delete_cword()

    def insert_text(self, text):
        self._com.insert_text(text)

    def call_with_current_word(self, callback):
        return self._com.get_current_word(
                reply_handler=callback,
                error_handler=self.log.exception)

    def call_with_selection_or_word(self, callback):
        #FIXME: test for selection
        return self._com.get_current_word(
                reply_handler=callback,
                error_handler=self.log.exception)

    def call_with_selection(self, callback):
        return self._com.get_selection(
                reply_handler=callback,
                error_handler=self.log.exception)

    def set_path(self, path):
        return self._com.cd(path)

    def get_cursor_offset(self):
        return self._com.get_cursor_offset()

    get_cursor_position = get_cursor_offset

    def set_cursor_offset(self, offset):
        self._com.set_cursor_offset(offset, **_ignore)

    set_cursor_position = set_cursor_offset

    def define_sign_type(self, name, icon, linehl, text, texthl):
        self._com.define_sign(name, icon, linehl, text, texthl)

    def undefine_sign_type(self, name):
        self._com.undefine_sign(name)

    def show_sign(self, type, filename, line):
        self._sign_index += 1
        self._signs[(filename, line, type)] = self._sign_index
        self._com.show_sign(self._sign_index, type, filename, line)

    def hide_sign(self, type, filename, line):
        try:
            index = self._signs.pop((filename, line, type))
            self._com.hide_sign(index, filename)
        except KeyError:
            self.window.error_dlg(_('Tried to remove non-existent sign'))

    def stop(self):
        self._com.quit(reply_handler=lambda *a: None,
                       error_handler=lambda *a: None)
        return

    #FIXME list of missing functions

    #def set_content(self, editor, value)
    #def get_content(self, editor)
    #def get_documentation

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
            import pty
            master, slave = pty.openpty()
            p = subprocess.Popen(
                    ['gvim', '--version'],
                    stdout=subprocess.PIPE,
                    stderr=slave,
                    )
            data, _ = p.communicate()
            if '+python' not in data:
                errors.extend([
                    'gvim lacks python support',
                    'please install gvim with python support'

                ])
        except OSError:
            errors.extend([
                'gvim not found',
                'please install gvim with python support'
            ])
        return errors


# Required Service attribute for service loading
Service = Vim


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

