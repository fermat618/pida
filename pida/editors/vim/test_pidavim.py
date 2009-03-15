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


def _start_vim():
    env = os.environ.copy()
    env['PIDA_DBUS_UUID'] = 'pidatest'
    p = subprocess.Popen(['gvim', '-iconic', '-f', '--cmd', 'so %s' % vim_script],
                         env=env)
    return p


def _make_test_file():
    fd, fn = tempfile.mkstemp(prefix='pidavim-tests-')
    os.write(fd, 'This is some test text\n')
    os.close(fd)
    return fn


class TestVim(object):

    def setUp(self):
        self.vim_process = _start_vim()
        time.sleep(1)
        self.vim = get_vim('pidatest')
        refresh_ui()

        self.files = [_make_test_file() for i in range(5)]

    def tearDown(self):
        for fn in self.files:
            os.unlink(fn)
        # XXX this segfaults for some reason
        # XXX self.vim.quit()
        # XXX so really kill the thing
        os.kill(self.vim_process.pid, 9)

        self.vim_process.wait()

    def test_eval(self):
        # vim-python is broken with regards evaling numbers as strings
        assert self.vim.eval('2 + 2') == '4'

    def test_command(self):
        self.vim.command('e %s' % self.files[0])
        assert self.vim.get_current_buffer() == self.files[0]

    def test_cursor(self):
        assert self.vim.get_cursor() == [1, 0]

    def test_set_cursor(self):
        self.vim.open_file(self.files[0])
        self.vim.set_cursor(1, 5)
        refresh_ui()
        assert self.vim.get_cursor() == [1, 5]

    def test_open_file(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        assert self.files[0] in self.vim.get_buffer_list()

    def test_open_files(self):
        self.vim.open_files(self.files)
        refresh_ui()
        for fn in self.files:
            assert fn in self.vim.get_buffer_list()

    def test_current_buffer(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        buffer = self.vim.get_current_buffer()

    def test_buffer_name(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        buffer = self.vim.get_current_buffer()
        assert buffer == self.files[0]

    def test_buffer_number(self):
        self.vim.open_file(self.files[0])
        self.vim.open_file(self.files[1])
        assert self.vim.get_buffer_number(self.files[0]) == 1
        assert self.vim.get_buffer_number(self.files[1]) == 2

    def test_open_buffer(self):
        self.vim.open_file(self.files[0])
        self.vim.open_file(self.files[1])
        self.vim.open_buffer(self.files[0])
        assert self.vim.get_current_buffer() == self.files[0]

    def test_close_buffer(self):

        will_close, stay_open = self.files[:2]

        self.vim.open_file(will_close)
        self.vim.open_file(stay_open)
        self.vim.close_buffer(will_close)

        buffer_list = list(self.vim.get_buffer_list())

        refresh_ui()

        assert stay_open in buffer_list
        assert will_close not in buffer_list

    def test_close_current_buffer(self):

        will_close, stay_open = self.files[:2]

        self.vim.open_file(stay_open)
        self.vim.open_file(will_close)

        self.vim.close_current_buffer()
        buffer_list = list(self.vim.get_buffer_list())

        refresh_ui()

        assert stay_open in buffer_list
        assert will_close not in buffer_list

    def test_save(self):
        self.vim.open_file(self.files[0])
        self.vim.append_at_cursor('hooo')
        self.vim.save_current_buffer()

    def test_save_as(self):
        self.vim.open_file(self.files[0])
        self.vim.append_at_cursor('hooo')
        self.vim.save_as_current_buffer(self.files[1])
        assert self.vim.get_current_buffer() == self.files[1]


    def test_current_line(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        assert self.vim.get_current_line() == 'This is some test text'

    def test_current_character(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        assert self.vim.get_current_character() == 'T'

    def test_insert_text_at_cursor(self):
        self.vim.insert_at_cursor("hello")
        self.vim.insert_at_cursor("hello")
        assert self.vim.get_current_line() == 'hellhelloo'

    def test_append_text_at_cursor(self):
        self.vim.append_at_cursor("hello")
        self.vim.append_at_cursor("hello")
        assert self.vim.get_current_line() == 'hellohello'

    def test_append_text_at_linened(self):
        self.vim.append_at_cursor("hello")
        self.vim.set_cursor(1, 0)
        self.vim.append_at_lineend("byebye")
        assert self.vim.get_current_line() == 'hellobyebye'

    def test_insert_text_at_linestart(self):
        self.vim.append_at_cursor("hello")
        self.vim.set_cursor(1, 0)
        self.vim.insert_at_linestart("byebye")
        assert self.vim.get_current_line() == 'byebyehello'

    def test_current_word(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        assert self.vim.get_current_word() == 'This'

    def test_replace_current_word(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        self.vim.replace_current_word('Banana')
        assert self.vim.get_current_word() == 'Banana'

    def test_select_current_word(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        self.vim.select_current_word()
        assert self.vim.eval('getreg("*")') == 'This'

    def test_get_selection(self):
        self.vim.open_file(self.files[0])
        refresh_ui()
        self.vim.select_current_word()
        assert self.vim.get_selection() == 'This'

    def test_copy(self):
        self.vim.open_file(self.files[0])
        self.vim.select_current_word()
        self.vim.copy()
        refresh_ui()
        assert gtk.clipboard_get().wait_for_text() == 'This'

    def test_cut(self):
        self.vim.open_file(self.files[0])
        self.vim.select_current_word()
        self.vim.cut()
        refresh_ui()
        assert gtk.clipboard_get().wait_for_text() == 'This'
        assert self.vim.get_current_line() == ' is some test text'

    def test_paste(self):
        self.vim.insert_at_cursor('hello')
        self.vim.select_current_word()
        self.vim.cut()
        self.vim.paste()
        refresh_ui()

        # XXX
        # Can't use the clipboard, because blocks on get
        # gtk.clipboard_get().set_text('banana')

        assert self.vim.get_current_line() == 'hello'

    def test_undo(self):
        self.vim.insert_at_cursor('hello')
        self.vim.undo()
        assert self.vim.get_current_line() == ''

    def test_redo(self):
        self.vim.insert_at_cursor('hello')
        self.vim.undo()
        self.vim.redo()
        assert self.vim.get_current_line() == 'hello'




