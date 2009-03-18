
" Vim Remote Communication
" Requires +python PyGTK and Python DBUS

set nocompatible

silent function! VimSignal(name, ...)
    python getattr(service, vim.eval('a:name'))(*clean_signal_args(vim.eval('a:000')))
endfunction


python << endpython
"""
Vim Integration for PIDA
"""

# Do this before we even breath

import os, sys
import vim

#sys.path.insert(0, os.path.dirname(vim.eval('$PIDA_PATH')))

import gtk, gobject

import dbus
import dbus.service

from dbus import SessionBus

from dbus.service import Object, method, signal, BusName

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

from pida.utils.pdbus import PidaRemote


DBUS_NS = 'uk.co.pida.vim'

def clean_signal_args(args):
    args = list(args)
    for i, arg in enumerate(args):
        if arg is None:
            args[i] = ''
    return args

class VimDBUSService(Object):

    def __init__(self, uid):
        bus_name = BusName('.'.join([DBUS_NS, uid]), bus=SessionBus())
        self.dbus_uid = uid
        self.dbus_path = '/vim'
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
        vim.command('confirm e %s' % path)

    @method(DBUS_NS, in_signature='as')
    def open_files(self, paths):
        for path in paths:
            self.open_file(path)

    # Buffer list

    @method(DBUS_NS, out_signature='as')
    def get_buffer_list(self):
        # vim's buffer list also contains unlisted buffers
        # we don't want those
        return [
            buffer.name for buffer in vim.buffers
            if int(vim.eval("buflisted(%s)"%buffer.number))
        ]

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

    @method(DBUS_NS, in_signature='i')
    def goto_line(self, linenumber):
        vim.command('%s' % linenumber)
        vim.command('normal zzzv')

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

    @method(DBUS_NS, in_signature='sssss')
    def define_sign(self, name, icon, linehl, text, texthl):
        cmd = ('sign define %s icon=%s linehl=%s text=%s texthl=%s '%
                             (name, icon, linehl, text, texthl))
        vim.command(cmd)

    @method(DBUS_NS, in_signature='s')
    def undefine_sign(self, name):
        vim.command('sign undefine %s' % name)

    @method(DBUS_NS, in_signature='issi')
    def show_sign(self, index, type, filename, line):
        vim.command('sign place %s line=%s name=%s file=%s' %
                             (index + 1, line, type, filename))

    @method(DBUS_NS, in_signature='is')
    def hide_sign(self, index, filename):
        vim.command('sign unplace %s' % (index + 1))

    @method(DBUS_NS, in_signature='i')
    def set_cursor_offset(self, offset):
        vim.current.window.cursor = _offset_to_position(offset)

    @method(DBUS_NS, out_signature='i')
    def get_cursor_offset(self):
        return get_offset()
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

    @signal(DBUS_NS)
    def SwapExists(self):
        pass

uid = vim.eval('$PIDA_DBUS_UUID')


service = VimDBUSService(uid)
client = PidaRemote(uid)

def get_offset():
    result = _position_to_offset(*vim.current.window.cursor)
    return result

def _position_to_offset(lineno, colno):
    result = colno
    for line in vim.current.buffer[:lineno-1]:
        result += len(line) + 1
    return result

def _offset_to_position(offset):
    text = '\n'.join(vim.current.buffer) + '\n'
    lineno = text.count('\n', 0, offset) + 1
    try:
        colno = offset - text.rindex('\n', 0, offset) - 1
    except ValueError:
        colno = offset
    return lineno, colno


def get_completions(base):
    b = '\n'.join(vim.current.buffer)
    o = int(vim.eval("s:pida_completion_offset"))
    c = client.call('language', 'get_completions', base, b, o)
    c = [str(i) for i in c]
    vim.command('let s:pida_completions = %r' % c)

def is_keyword_char(c):
    return c.isalnum() or (c in '_')

def set_start_var(col):
    vim.command('let s:pida_completion_start = %r' % (col + 1))

def find_start():
    o = get_offset()
    vim.command('let s:pida_completion_offset = %r' % o)

    # we have to find the start of the word to replace
    # we could use rope, but we want an inclusive thing

    # get the cursor position
    row, col = vim.current.window.cursor

    # now row is index 1, and column is index 0,
    # But(!) column can be len(line)

    # current line
    l = vim.current.buffer[row - 1]

    # we are on the first character of the line
    if col == 0:
        set_start_var(col)
    else:
        col = col - 1
        c = l[col]
        while is_keyword_char(c) and col > 0:
            col -= 1
            c = l[col]
        set_start_var(col)


    #vim.command('let s:pida_completion_start = %r' % (col + 1))







endpython

" Completion function

silent function! Find_Start()
" locate the start of the word
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\a'
        let start -= 1
    endwhile
    return start

endfunction


silent function! Pida_Complete(findstart, base)
    " locate the start of the word
    if a:findstart
        python find_start()
	    return s:pida_completion_start
    else
        python get_completions(vim.eval('a:base'))
        return s:pida_completions
    endif
endfunction
set completefunc=Pida_Complete



function! CleverTab()
    if pumvisible()
        return "\<C-N>"
    endif
    let col = col('.') - 1
    if strpart( getline('.'), 0, col('.')-1 ) =~ '^\s*$'
        return "\<Tab>"
    elseif getline('.')[col - 1] !~ '\.'
        return "\<C-N>"
    else
        return "\<C-X>\<C-U>"
    endif
endfunction
inoremap <expr> <TAB> CleverTab()


" Now the vim events
silent augroup VimCommsDBus
silent au! VimCommsDBus
silent au VimCommsDBus BufEnter * silent call VimSignal('BufEnter')
silent au VimCommsDBus BufDelete * silent call VimSignal('BufDelete', expand('<amatch>'))
silent au VimCommsDBus VimLeave * silent call VimSignal('VimLeave')
silent au VimCommsDBus VimEnter * silent call VimSignal('VimEnter')
silent au VimCommsDBus BufWritePost * silent call VimSignal('BufWritePost')
silent au VimCommsDBus CursorMovedI,CursorMoved * silent call VimSignal('CursorMoved')
silent au VimCommsDBus SwapExists * silent call VimSignal('SwapExists')

" Some UI Stuffs
set nomore
set guioptions-=T
set guioptions-=m
set guioptions+=c


