
" Vim Remote Communication
" Requires +python PyGTK and Python DBUS


silent function! VimSignal(name, ...)
    python getattr(service, vim.eval('a:name'))(*clean_signal_args(vim.eval('a:000')))
endfunction


python << endpython
"""
Vim Integration for PIDA
"""

import vim

import gtk, gobject

import dbus
import dbus.service

from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop

from dbus.service import Object, method, signal, BusName

DBusGMainLoop(set_as_default=True)

DBUS_NS = 'uk.co.pida.vim'

def create_path(uid):
    return '/uk/co/pida/vim/%s' % uid

def clean_signal_args(args):
    args = list(args)
    for i, arg in enumerate(args):
        if arg is None:
            args[i] = ''
    return args

class VimDBUSService(Object):

    def __init__(self, uid):
        bus_name = BusName(DBUS_NS, bus=SessionBus())
        self.dbus_uid = uid
        self.dbus_path = create_path(uid)
        dbus.service.Object.__init__(self, bus_name, self.dbus_path)

    # Basic interface

    @method(DBUS_NS, in_signature='s')
    def command(self, c):
        return vim.command(c)

    @method(DBUS_NS, in_signature='s')
    def eval(self, e):
        return vim.eval(e)

    # simple commands

    @method(DBUS_NS, in_signature='s')
    def echo(self, s):
        vim.command('echo "%s"' % s)

    # File opening

    @method(DBUS_NS, in_signature='s')
    def open_file(self, path):
        vim.command('e %s' % path)

    @method(DBUS_NS, in_signature='as')
    def open_files(self, paths):
        for path in paths:
            self.open_file(path)

    # Buffer list

    @method(DBUS_NS, out_signature='as')
    def get_buffer_list(self):
        return [b.name for b in vim.buffers]

    @method(DBUS_NS, in_signature='s', out_signature='i')
    def get_buffer_number(self, path):
        return int(vim.eval("bufnr('%s')" % path))


    @method(DBUS_NS, in_signature='s')
    def open_buffer(self, path):
        vim.command('b!%s' % self.get_buffer_number(path))

    # Saving

    @method(DBUS_NS)
    def save_current_buffer(self):
        vim.command('w')

    @method(DBUS_NS, in_signature='s')
    def save_as_current_buffer(self, path):
        vim.command('saveas! %s' % path)

    # Closing

    @method(DBUS_NS, in_signature='s')
    def close_buffer(self, path):
        vim.command('confirm bd%s' % self.get_buffer_number(path))

    @method(DBUS_NS)
    def close_current_buffer(self):
        vim.command('confirm bd')

    # Current cursor

    @method(DBUS_NS, out_signature='ai')
    def get_cursor(self):
        return vim.current.window.cursor

    @method(DBUS_NS, in_signature='ii')
    def set_cursor(self, row, column):
        vim.current.window.cursor = (row, column)

    @method(DBUS_NS, out_signature='s')
    def get_current_buffer(self):
        return vim.current.buffer.name or ''

    @method(DBUS_NS)
    def quit(self):
        vim.command('q!')

    @method(DBUS_NS)
    def get_current_line(self):
        return vim.current.buffer[vim.current.window.cursor[0] - 1]

    @method(DBUS_NS)
    def get_current_character(self):
        y, x = vim.current.window.cursor
        return self.get_current_line()[x]

    @method(DBUS_NS, in_signature='s')
    def insert_at_cursor(self, text):
        vim.command("normal i%s" % text)

    @method(DBUS_NS, in_signature='s')
    def append_at_cursor(self, text):
        vim.command("normal a%s" % text)

    @method(DBUS_NS, in_signature='s')
    def insert_at_linestart(DBUS_NS, text):
        vim.command("normal I%s" % text)

    @method(DBUS_NS, in_signature='s')
    def append_at_lineend(DBUS_NS, text):
        vim.command("normal A%s" % text)

    @method(DBUS_NS, out_signature='s')
    def get_current_word(self):
        return vim.eval('expand("<cword>")')

    @method(DBUS_NS, out_signature='s')
    def get_cwd(self):
        return vim.eval('getcwd()')

    @method(DBUS_NS, in_signature='s')
    def cut_current_word(self, text):
        vim.command('normal ciw%s' % text)

    @method(DBUS_NS, in_signature='s')
    def replace_current_word(self, text):
        vim.command('normal ciw%s' % text)

    @method(DBUS_NS, in_signature='s', out_signature='s')
    def get_register(self, name):
        return vim.eval('getreg("%s")' % name)

    @method(DBUS_NS)
    def select_current_word(self):
        vim.command('normal viw')

    @method(DBUS_NS, out_signature='s')
    def get_selection(self):
        return self.get_register('*')

    @method(DBUS_NS)
    def copy(self):
        vim.command('normal "+y')

    @method(DBUS_NS)
    def cut(self):
        vim.command('normal "+x')

    @method(DBUS_NS)
    def paste(self):
        vim.command('normal "+p')

    @method(DBUS_NS)
    def undo(self):
        vim.command('undo')

    @method(DBUS_NS)
    def redo(self):
        vim.command('redo')

    @method(DBUS_NS, in_signature='s')
    def set_colorscheme(self, name):
        vim.command('colorscheme %s' % name)

    @method(DBUS_NS, in_signature='si')
    def set_font(self, name, size):
        vim.command('set guifont=%s\\ %s' % (name, size))

    @method(DBUS_NS, in_signature='s')
    def cd(self, path):
        vim.command('cd %s' % path)

    # Signals

    @signal(DBUS_NS)
    def BufEnter(self):
        pass

    @signal(DBUS_NS, signature='s')
    def BufDelete(self, filename):
        print 'BufDelete'

    @signal(DBUS_NS)
    def VimEnter(self):
        pass

    @signal(DBUS_NS)
    def VimLeave(self):
        pass

    @signal(DBUS_NS)
    def BufWritePost(self):
        pass

    @signal(DBUS_NS)
    def CursorMoved(self):
        pass

print vim.eval('$PIDA_DBUS_UID')
service = VimDBUSService(vim.eval('$PIDA_DBUS_UID'))

endpython



" Now the vim events
silent augroup VimCommsDBus
silent au! VimCommsDBus
silent au VimCommsDBus BufEnter * silent call VimSignal('BufEnter')
silent au VimCommsDBus BufDelete * silent call VimSignal('BufDelete', expand('<amatch>'))
silent au VimCommsDBus VimLeave * silent call VimSignal('VimLeave')
silent au VimCommsDBus VimEnter * silent call VimSignal('VimEnter')
silent au VimCommsDBus BufWritePost * silent call VimSignal('BufWritePost')
silent au VimCommsDBus CursorMovedI,CursorMoved * silent call VimSignal('CursorMoved')

" Some UI Stuffs

set guioptions-=T
set guioptions-=m


