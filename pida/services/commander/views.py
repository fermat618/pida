
import os
import subprocess

import gtk
import gobject

from pygtkhelpers.gthreads import AsyncTask

from pida.utils import ostools
from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal
from pida.ui.buttons import create_mini_button


class TerminalView(PidaView):

    icon_name = 'terminal'

    def create_ui(self):
        self._pid = None
        self._is_alive = False
        self._last_cwd = None
        self._hb = gtk.HBox()
        self._hb.show()
        self.add_main_widget(self._hb)
        self._term = PidaTerminal(**self.svc.get_terminal_options())
        #self._matchids = {}
        #for match, callback in self.svc.features['matches']:
        #    i = self._term.match_add(match)
        #    if i < 0:
        #        continue
        #    self._term.match_set_cursor_type(i, gtk.gdk.HAND2)
        #    self._matchids[i] = match
        self._term.parent_view = self
        self._term.connect('window-title-changed', self.on_window_title_changed)
        self._term.connect('selection-changed', self.on_selection_changed)
        #self._term.connect('button_press_event', self.on_button_pressed)
        self._term.show()
        self._create_scrollbar()
        self._create_bar()
        self._hb.pack_start(self._term)
        if self.svc.opt('scrollbar_visible'):
            self._hb.pack_start(self._scrollbar, expand=False)
        self._hb.pack_start(self._bar, expand=False)
        self.master = None
        self.slave = None
        self._init_matches()
        #self.prep_highlights()

    def _init_matches(self):
        for args in self.svc.features['match']:
            self._term.match_add_match(usr=self, *args)
        for args in self.svc.features['match-callback']:
            self._term.match_add_callback(usr=self, *args)
        for args in self.svc.features['match-menu']:
            self._term.match_add_menu(usr=self, *args)
        for args in self.svc.features['match-menu-callback']:
            self._term.match_add_menu_callback(usr=self, *args)

    def _create_scrollbar(self):
        self._scrollbar = gtk.VScrollbar()
        self._scrollbar.set_adjustment(self._term.get_adjustment())
        self._scrollbar.show()

    def _create_bar(self):
        self._bar = gtk.VBox(spacing=1)
        self._stick_button = create_mini_button(
            'pin', _('Automatic change to the current buffer\'s directory'),
            None, toggleButton=True)
        self._bar.pack_start(self._stick_button, expand=False)
        self._copy_button = create_mini_button(
            gtk.STOCK_COPY, _('Copy the selection to the clipboard'),
            self.on_copy_clicked)
        self._copy_button.set_sensitive(False)
        self._bar.pack_start(self._copy_button, expand=False)
        self._paste_button = create_mini_button(
            gtk.STOCK_PASTE, _('Paste the contents of the clipboard'),
            self.on_paste_clicked)
        self._bar.pack_start(self._paste_button, expand=False)
        self._title = gtk.Label()
        self._title.set_alignment(0.5, 1)
        self._title.set_padding(0, 3)
        self._title.set_angle(270)
        self._title.set_size_request(0,0)
        self._bar.pack_start(self._title)
        self._bar.show_all()

    def execute(self, commandargs, env, cwd, eof_handler=None,
                use_python_fork=False, parser_func=None):
        title_text = ' '.join(commandargs)
        self._is_alive = True
        self._title.set_text(title_text)
        if eof_handler is None:
            self.eof_handler = self.on_exited
        else:
            def eof_wrapper(*args, **kwargs):
                self._is_alive = False
                eof_handler(self, *args, **kwargs)
            self.eof_handler = eof_wrapper
        if use_python_fork:
            if parser_func == None:
                self._python_fork(commandargs, env, cwd)
            else:
                self._python_fork_parse(commandargs, env, cwd, parser_func)
        else:
            self._vte_fork(commandargs, env, cwd)

    def _python_fork_waiter(self, popen):
        exit_code = popen.wait()
        return exit_code

    def _python_fork_complete(self, exit_code):
        gobject.timeout_add(200, self.eof_handler, self._term)

    def _python_fork_preexec_fn(self):
        os.setpgrp()

    def _python_fork(self, commandargs, env, cwd):
        self._term.connect('commit', self.on_commit_python)
        # TODO: Env broken
        env = dict(os.environ)
        env['TERM'] = 'xterm'
        (master, slave) = os.openpty()
        self.slave = slave
        self.master = master
        self._term.set_pty(master)
        p = subprocess.Popen(commandargs, stdin=slave, stdout=slave,
                             preexec_fn=self._python_fork_preexec_fn,
                             stderr=slave, env=env, cwd=cwd, close_fds=True)
        self._pid = p.pid
        self._last_cwd = cwd
        gobject.timeout_add(200, self._save_cwd)
        t = AsyncTask(self._python_fork_waiter, self._python_fork_complete)
        t.start(p)

    def _python_fork_parse(self, commandargs, env, cwd, parser_func):
        self._term.connect('commit', self.on_commit_python)
        env = dict(os.environ)
        env['TERM'] = 'xterm'
        master, self.slave = os.openpty()
        self._term.set_pty(master)
        self.master, slave = os.openpty()
        p = subprocess.Popen(commandargs, stdout=slave,
                         stderr=subprocess.STDOUT, stdin=slave,
                         close_fds=True)
        self._pid = p.pid
        self._last_cwd = cwd
        gobject.timeout_add(200, self._save_cwd)
        gobject.io_add_watch(self.master, gobject.IO_IN, 
                                self._on_python_fork_parse_stdout, parser_func)
        self._term.connect('key-press-event',
                            self._on_python_fork_parse_key_press_event, self.master)

    def _on_python_fork_parse_key_press_event(self, term, event, fd):
        mapping = {
                22: '\x7f',
                98: "\x1bOA",
                104:"\x1bOB",
                100:"\x1bOD",
                102:"\x1bOC",
                }
        os.write(fd, mapping.get(event.hardware_keycode, event.string))
        return True

    def _on_python_fork_parse_stdout(self, fd, state, parser = None):
        data = os.read(fd,1024)
        os.write(self.slave, data)
        if parser != None:
            parser(data)
        return True

    def _vte_env_map_to_list(self, env):
        return ['%s=%s' % (k, v) for (k, v) in env.items()]

    def _vte_fork(self, commandargs, env, cwd):
        self._term.connect('child-exited', self.eof_handler)
        self._pid = self._term.fork_command(commandargs[0], commandargs, env, cwd)
        self._last_cwd = cwd
        gobject.timeout_add(200, self._save_cwd) 

    def close_view(self):
        self.svc.boss.cmd('window', 'remove_view', view=self)

    def on_exited(self, term):
        self._is_alive = False
        self._term.feed_text(_('Child exited')+'\r\n', '1;34')
        self._term.feed_text(_('Press Enter/Space key to close.'))
        self._term.connect('commit', self.on_press_any_key)

    def can_be_closed(self):
        self.kill()
        return True

    def kill(self):
        if self._pid is not None:
            try:
                ostools.kill_pid(self._pid)
            except (ostools.NoSuchProcess, ostools.AccessDenied):
                self.svc.log.debug('PID {pid} has already gone', pid=self._pid)

    def on_button_pressed(self, term, event):
        if not event.button in [1,2] or \
           not event.state & gtk.gdk.CONTROL_MASK:
            return
        line = int(event.y/self._term.get_char_height())
        col = int(event.x/self._term.get_char_width())
        chk = self._term.match_check(col, line)
        if not chk: 
            return

        (match, matchfun) = chk
        if match and self._matchids.has_key(matchfun):
            callbacks = self.svc.get_match_callbacks(self._matchids[matchfun])
            for call in callbacks:
                if call(self, event, match):
                    return

    def on_selection_changed(self, term):
        self._copy_button.set_sensitive(self._term.get_has_selection())

    def on_copy_clicked(self, button):
        self._term.copy_clipboard()

    def on_paste_clicked(self, button):
        self._term.paste_clipboard()

    def on_press_any_key(self, term, data, datalen):
        if data == "\r" or data == " ":
            self.close_view()

    def on_commit_python(self, term, data, datalen):
        if data == '\x03':
            ostools.kill_pid(self._pid, 2)

    def on_window_title_changed(self, term):
        self._title.set_text(term.get_window_title())

    def chdir(self, path):
        """
        Try to change into the new directory.
        Used by pin terminals for example.
        """
        if ostools.get_cwd(self._pid) == path:
            return
        # maybe we find a good way to check if the term is currently
        # in shell mode and maybe there is a better way to change
        # directories somehow
        # this is like kate does it
        self._term.feed_child(u'cd %s\n' %path)

    def _save_cwd(self):
        try:
            self._last_cwd = ostools.get_cwd(self._pid)
            return True
        except (ostools.NoSuchProcess, ostools.AccessDenied):
            return False

    def get_absolute_path(self, path):
        """
        Return the absolute path for path and the terminals cwd
        """
        try:
            return ostools.get_absolute_path(path, self._pid)
        except (ostools.NoSuchProcess, ostools.AccessDenied):
            if self._last_cwd:
                apath = os.path.abspath(os.path.join(self._last_cwd, path))
                if os.path.exists(apath):
                    return apath

    @property
    def is_alive(self):
        return self._is_alive

class PythonView(PidaView):

    icon_name = 'terminal'
    focus_ignore = True

    def create_ui(self):
        self.pid = None
        self.box = gtk.HBox()
        self.socket = gtk.Socket()
        self.box.add(self.socket)
        self.socket.show()
        self.box.show()
        self.add_main_widget(self.box)

    def on_socket__plug_removed(self, *k):
        self.box.remove(self.socket)
        l = gtk.Label('BPython was shut down')
        l.show()
        self.box.add(l)

    def execute(self, file_=None, cwd=os.getcwd()):
        commandargs = [
            'bpython-gtk',
            '--socket-id=%s' % self.socket.get_id(),
            ]
        if file_:
            commandargs.extend(['-i', file_])
        self.popen = p = subprocess.Popen(commandargs, cwd=cwd)
        self._pid = p.pid

    def can_be_closed(self):
        self.kill()
        return True

    def kill(self):
        if self._pid is not None:
            try:
                ostools.kill_pid(self._pid)
            except ostools.NoSuchProcess:
                self.svc.log_debug('PID {pid} has already gone', pid=self._pid)




from .commander import _ #XXX: hack
