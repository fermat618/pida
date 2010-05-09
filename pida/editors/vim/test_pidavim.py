# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os, time, subprocess, tempfile

import gtk, dbus

from dbus.mainloop.glib import DBusGMainLoop
import logging
from .client import get_vim, log
log.setLevel(logging.WARNING)

mainloop = DBusGMainLoop(set_as_default=True)
vim_script = os.path.abspath('pida/resources/data/pida.vim')

def refresh_ui():
    while gtk.events_pending():
        gtk.main_iteration_do(False)


def _start_vim(sid, uuid):
    env = os.environ.copy()
    env['PIDA_DBUS_UUID'] = uuid
    env['PIDA_PATH'] = '.'
    p = subprocess.Popen([
        'gvim', '--socketid', str(sid), '-f',
        '--cmd', 'so %s' % vim_script],
        env=env)
    return p

def pytest_funcarg__vim_process(request):
    w = gtk.Window()
    w.set_title(request.function.__name__)
    s = gtk.Socket()
    w.add(s)
    w.set_size_request(600, 600)
    w.show_all()
    refresh_ui()
    process = _start_vim(
            s.get_id(),
            request.function.__name__)
    process._win_ = w
    request.addfinalizer(w.destroy)
    return process

def pytest_funcarg__vim(request):
    process = request.getfuncargvalue('vim_process')
    vim = get_vim(request.function.__name__)
    refresh_ui()
    def quit():
        try:
            vim.quit(ignore_reply=True)
        except: #XXX: its dead :)
            pass
    request.addfinalizer(quit)
    return vim


def pytest_funcarg__files(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    files = [tmpdir.ensure('file_%s.txt' % i) for i in range(5)]
    for file in files:
        file.write('This is some test text\n')
    return [str(x) for x in files]

def test_get_cwd(vim):
    path = vim.get_cwd()

def test_quit(vim):
    vim.quit(ignore_reply=True)

def test_eval(vim):
    # vim-python is broken with regards evaling numbers as strings
    assert vim.eval('2 + 2') == '4'

def test_command(vim, files):
    vim.command('e %s' % files[0])
    assert vim.get_current_buffer() == files[0]

def test_cursor(vim):
    assert vim.get_cursor() == [1, 0]

def test_open_file(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    buffers = vim.get_buffer_list()

    assert files[0] in buffers

def test_open_files(vim, files):
    for file in files:
        vim.open_file(file)
        refresh_ui()
    refresh_ui()
    buffers = vim.get_buffer_list()
    assert buffers == files

def test_set_cursor(vim, files):
    vim.open_file(files[0])
    vim.set_cursor(1, 5)
    refresh_ui()
    assert vim.get_cursor() == [1, 5]

def test_current_buffer(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    buffer = vim.get_current_buffer()

def test_buffer_name(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    buffer = vim.get_current_buffer()
    assert buffer == files[0]

def test_buffer_number(vim, files):
    vim.open_file(files[0])
    vim.open_file(files[1])
    assert vim.get_buffer_number(files[0]) == 1
    assert vim.get_buffer_number(files[1]) == 2

def test_open_buffer(vim, files):
    vim.open_file(files[0])
    vim.open_file(files[1])
    vim.open_buffer(files[0])
    assert vim.get_current_buffer() == files[0]

def test_close_buffer(vim, files):

    will_close, stay_open = files[:2]

    vim.open_file(will_close)
    vim.open_file(stay_open)
    vim.close_buffer(will_close)

    buffer_list = list(vim.get_buffer_list())

    refresh_ui()

    assert stay_open in buffer_list
    assert will_close not in buffer_list

def test_close_current_buffer(files, vim):

    will_close, stay_open = files[:2]

    vim.open_file(stay_open)
    vim.open_file(will_close)

    vim.close_current_buffer()
    buffer_list = list(vim.get_buffer_list())

    refresh_ui()

    assert stay_open in buffer_list
    assert will_close not in buffer_list

def test_save(vim, files):
    vim.open_file(files[0])
    vim.append_at_cursor('hooo')
    vim.save_current_buffer()

def test_save_as(vim, files):
    vim.open_file(files[0])
    vim.append_at_cursor('hooo')
    refresh_ui()
    vim.save_as_current_buffer(files[1])
    assert vim.get_current_buffer() == files[1]

def test_current_line(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    assert vim.get_current_line() == 'This is some test text'

def test_current_character(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    assert vim.get_current_character() == 'T'

def test_insert_text_at_cursor(vim):
    vim.insert_at_cursor("hello")
    vim.insert_at_cursor("hello")
    assert vim.get_current_line() == 'hellhelloo'

def test_append_text_at_linened(vim):
    vim.append_at_cursor("hello")
    vim.set_cursor(1, 0)
    vim.append_at_lineend("byebye")
    assert vim.get_current_line() == 'hellobyebye'

def test_insert_text_at_linestart(vim):
    vim.append_at_cursor("hello")
    vim.set_cursor(1, 0)
    vim.insert_at_linestart("byebye")
    assert vim.get_current_line() == 'byebyehello'

def test_current_word(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    assert vim.get_current_word() == 'This'

def test_replace_current_word(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    vim.replace_current_word('Banana')
    assert vim.get_current_word() == 'Banana'

def test_select_current_word(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    vim.select_current_word()
    val = vim.get_selection()
    assert val == 'This'

def test_get_selection(vim, files):
    vim.open_file(files[0])
    refresh_ui()
    vim.select_current_word()
    assert vim.get_selection() == 'This'

def test_copy(vim, files):
    vim.open_file(files[0])
    vim.select_current_word()
    vim.copy()
    refresh_ui()
    assert gtk.clipboard_get().wait_for_text() == 'This'

def test_cut(vim, files):
    vim.open_file(files[0])
    vim.select_current_word()
    refresh_ui()
    vim.cut()
    refresh_ui()
    assert gtk.clipboard_get().wait_for_text() == 'This'
    assert vim.get_current_line() == ' is some test text'

def test_paste(vim):
    vim.insert_at_cursor('hello')
    vim.select_current_word()
    vim.cut()
    vim.paste()
    refresh_ui()

    # XXX
    # Can't use the clipboard, because blocks on get
    # gtk.clipboard_get().set_text('banana')

    assert vim.get_current_line() == 'hello'

def test_redo(vim):
    vim.insert_at_cursor('hello')
    vim.undo()
    vim.redo()
    assert vim.get_current_line() == 'hello'

def test_undo(vim):
    vim.insert_at_cursor('hello')
    vim.undo()
    assert vim.get_current_line() == ''



