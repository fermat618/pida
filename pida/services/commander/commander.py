# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os, subprocess, re, sys

import gtk
import gtk.gdk
import gobject
import pango

# PIDA Imports
import pida
from pida.core import environment
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.utils.gthreads import AsyncTask
from pida.utils import ostools

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal
from pida.ui.buttons import create_mini_button

# locale
from pida.core.locale import Locale
locale = Locale('commander')
_ = locale.gettext


class CommanderOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'font',
            _('Terminal Font'),
            pango.Font,
            'Monospace 10',
            _('The font used in terminals'),
        )

        self.create_option(
            'transparent',
            _('Terminal Transparency'),
            bool,
            False,
            _('Whether terminals will be transparent'),
        )

        self.create_option(
            'use_background_image',
            _('Use a background image'),
            bool,
            False,
            _('Whether a background image will be displayed'),
        )

        self.create_option(
            'background_image_file',
            _('Background image file'),
            file,
            '',
            _('The file used for the background image'),
        )

        self.create_option(
            'cursor_blinks',
            _('Cursor Blinks'),
            bool,
            False,
            _('Whether the cursor will blink')
        )

        self.create_option(
            'scrollback_lines',
            _('Scrollback line numer'),
            int,
            100,
            _('The number of lines in the terminal scrollback buffer'),
        )

        self.create_option(
            'scrollbar_visible',
            _('Show terminal scrollbar'),
            bool,
            True,
            _('Whether a scrollbar should be shown'),
        )

        self.create_option(
            'allow_bold',
            _('Allow bold in the terminal'),
            bool,
            True,
            _('Whether bold text is allowed in the terminal'),
        )

        self.create_option(
            'audible_bell',
            _('Emit audible bell in terminal'),
            bool,
            False,
            _('Whether an audible bell will be emitted in the terminal'),
        )



        self.create_option(
            'shell_command',
            _('The shell command'),
            str,
            ostools.get_default_system_shell(),
            _('The command that will be used for shells')
        )

        self.create_option(
            'shell_command_args',
            _('The shell arguments'),
            list,
            [],
            _('The arguments to pass to the shell command'),
        )

        self.create_option(
            'python_path',
            _('Python Path'),
            str,
            sys.executable,
            _('Python executable to use'),
        )

        self.create_option(
            'use_ipython',
            _('Use IPython'),
            bool,
            False,
            _('Use IPython in python shell'),
        )


class CommanderActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'shell',
            TYPE_NORMAL,
            _('_Run Shell'),
            _('Open a shell prompt'),
            'terminal',
            self.execute_shell,
            '<Shift><Control>T',
        )

        self.create_action(
            'python_shell',
            TYPE_NORMAL,
            _('_Run Python Shell'),
            _('Open a python shell'),
            'terminal',
            self.execute_python_shell,
            '<Shift><Control>P',
        )

        self.create_action(
            'terminal-for-file',
            TYPE_NORMAL,
            _('Shell in file directory'),
            _('Open a shell prompt in the parent directory of this file'),
            'terminal',
            self.on_terminal_for_file,
        )

        self.create_action(
            'terminal-for-dir',
            TYPE_NORMAL,
            _('Shell in directory'),
            _('Open a shell prompt in the directory'),
            'terminal',
            self.on_terminal_for_dir,
        )

    def execute_shell(self, action):
        self.svc.cmd('execute_shell',
                     cwd=self.svc.get_current_project_directory())

    def execute_python_shell(self, action):
        self.svc.cmd('execute_python_shell',
                     cwd=self.svc.get_current_project_directory())


    def on_terminal_for_file(self, action):
        cwd = os.path.dirname(action.contexts_kw['file_name'])
        self.svc.cmd('execute_shell', cwd=cwd)

    def on_terminal_for_dir(self, action):
        cwd = action.contexts_kw['dir_name']
        self.svc.cmd('execute_shell', cwd=cwd)


class CommanderCommandsConfig(CommandsConfig):

    def execute(self, commandargs, env=[], cwd=os.getcwd(), title=_('Command'),
                      icon='terminal', eof_handler=None, use_python_fork=False,
                      parser_func=None):
        return self.svc.execute(commandargs, env, cwd, title, icon,
                                eof_handler, use_python_fork, parser_func)

    def execute_shell(self, env=[], cwd=os.getcwd(), title='Shell'):
        shell_command = self.svc.opt('shell_command')
        shell_args = self.svc.opt('shell_command_args')
        commandargs = [shell_command] + shell_args
        return self.svc.execute(commandargs, env=env, cwd=cwd, title=title, icon=None)

    def execute_python_shell(self, file_=None, cwd=os.getcwd(), ipython=None, title='Python'):
        if ipython is None:
            ipython = self.svc.opt('use_ipython')
        return self.svc.execute_python(file_=file_, cwd=cwd, title=title, icon=None)

class CommanderFeaturesConfig(FeaturesConfig):

    def create(self):
        self.publish('match', 'match-callback', 'match-menu', 'match-menu-callback')
        for match in ostools.PATH_MATCHES:
            self.subscribe('match-callback', ('File', match[0], match[1], 
                                              self.on_default_match))
            self.subscribe('match-menu-callback',
                ('dir-match',
                match[0], match[1],
                self.on_highlight_path))

        self.subscribe('match-menu-callback',
            ('url-match',
                r'https{0,1}://[A-Za-z0-9/\-\._]+',
                r'(https{0,1}://[A-Za-z0-9/\-\._]+)',
                self.on_highlight_url))
        self.subscribe('match-menu-callback',
            ('dir-match',
            r'~{0,1}(/|\./)[a-zA-Z/\-\._]+',
            r'(~{0,1}(/|\./)[A-Za-z0-9/\-\._]+)',
            self.on_highlight_path))

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc, 'commander-file-menu.xml'))
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc, 'commander-dir-menu.xml'))

    def _mkactlst(self, lst):
        rv = []
        for item in lst:
            act = item.get_action()
            if act:
                rv.append(act)
        return rv


    def on_highlight_url(self, term, event, url, *args, **kw):
        return self._mkactlst(self.svc.boss.cmd('contexts', 'get_menu', 
                                                context='url-menu', url=url))

    def on_highlight_path(self, term, event, path, *args, **kw):
        path = os.path.expanduser(path)
        line = None
        if path.find(":") != -1:
            path, line = path.rsplit(":", 1)
            try:
                 line = int(line)
            except ValueError:
                 line = None

        path = kw['usr'].get_absolute_path(path)

        if not path:
            return []

        if os.path.isdir(path):
            return self._mkactlst(self.svc.boss.cmd('contexts',
                                'get_menu', context='dir-menu', dir_name=path))
        elif os.path.isfile(path):
            return self._mkactlst(self.svc.boss.cmd('contexts', 
                              'get_menu', context='file-menu', file_name=path))
        else:
            return []

    def on_default_match(self, term, event, match, *args, **kwargs):
        match = os.path.expanduser(args[0])
        line = None
        if match.find(":") != -1:
            rfile_name, line = match.rsplit(":", 1)
            try:
                 line = int(line)
            except ValueError:
                 line = None
        else:
            rfile_name = match
        file_name = kwargs['usr'].get_absolute_path(rfile_name)

        if file_name and os.path.isfile(file_name):
            self.svc.boss.cmd('buffer', 'open_file', 
                                file_name=file_name,
                                line=line)
        elif file_name and os.path.isdir(file_name):
            self.svc.boss.cmd('filemanager', 'browse', 
                        new_path=file_name)
            self.svc.boss.cmd('filemanager', 'present_view')
        else:
            # fallback. look if there is a open file that matches this filename
            for doc in self.svc.boss.cmd('buffer', 
                                         'get_documents').itervalues():
                rfile_name = os.path.basename(rfile_name)
                if doc.basename == rfile_name:
                    self.svc.boss.cmd('buffer', 'open_file', 
                                        document=doc,
                                        line=line)
                    break


class CommanderEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
                               self.svc.set_current_project)
        self.subscribe_foreign('contexts', 'show-menu',
                               self.on_contexts__show_menu)
        self.subscribe_foreign('buffer', 'document-changed',
                               self.svc.on_buffer_change)

    def on_contexts__show_menu(self, menu, context, **kw):
        if (context == 'file-menu'):
            self.svc.get_action('terminal-for-file').set_visible(kw['file_name'] is not None)

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
                self.svc.log.debug('PID %s has already gone' % self._pid)

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
        self._box = gtk.HBox()
        self._socket = gtk.Socket()
        self._box.add(self._socket)
        self._socket.show()
        self._box.show()
        self.add_main_widget(self._box)

    def execute(self, file_=None, cwd=os.getcwd()):
        commandargs = [
            self.svc.opt('python_path'),
            '-m', 'bpython.gtk_',
            '--socket-id=%s' %self._socket.get_id(),
            ]
        if file_:
            commandargs.extend(['-i', file_])
        self.popen = p = subprocess.Popen(commandargs, cwd=cwd, close_fds=True)
        self._pid = p.pid

    def can_be_closed(self):
        self.kill()
        return True

    def kill(self):
        if self._pid is not None:
            try:
                ostools.kill_pid(self._pid)
            except ostools.NoSuchProcess:
                self.svc.log_debug('PID %s has already gone' % self._pid)

# Service class
class Commander(Service):
    """Executes programms in a terminal window or background""" 

    commands_config = CommanderCommandsConfig
    actions_config = CommanderActionsConfig
    options_config = CommanderOptionsConfig
    features_config = CommanderFeaturesConfig
    events_config = CommanderEvents

    def start(self):
        self._terminals = []
        self._matches = {}
        self.current_project = None

    def execute(self, commandargs, env, cwd, title, icon, eof_handler=None,
                use_python_fork=False, parser_func=None):
        env_pida = env[:]
        env_pida.append('PIDA_VERSION=%s' % pida.version)
        current_project = self.boss.cmd('project', 'get_current_project')
        if current_project:
            env_pida.append('PIDA_PROJECT=%s' % current_project.source_directory)
        t = TerminalView(self, title, icon)
        self.log.debug(" ".join((unicode(x) for x in ("execute", commandargs, 
                env_pida, cwd))))
        t.execute(commandargs, env_pida, cwd, eof_handler, use_python_fork, parser_func)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=t)
        t.pane.connect('remove', self._on_termclose)
        self._terminals.append(t)
        return t

    def execute_python(self, file_, cwd, title, icon):
        current_project = self.boss.cmd('project', 'get_current_project')
        #if current_project:
        #    env_pida.append('PIDA_PROJECT=%s' % current_project.source_directory)
        t = PythonView(self, title, icon)
        #t = TerminalView(self, title, icon)
        #self.log.debug(" ".join((unicode(x) for x in ("execute", commandargs, 
        #        env_pida, cwd))))
        #FIXME: we have to add it non detachable as dispatching
        # causes the socket to not be realized for a short time 
        # and therefor kills the process
        self.boss.cmd('window', 'add_view', paned='Terminal', view=t, detachable=False)
        t.execute(file_=None, cwd=cwd)
        self._terminals.append(t)
        t.pane.connect('remove', self._on_termclose)
        return t

    def _on_termclose(self, pane):
        for term in self._terminals:
            if term.pane == pane:
                self._terminals.remove(term)

    def get_terminal_options(self):
        options = dict(
            font_from_string=self.opt('font'),
            background_transparent=self.opt('transparent'),
            cursor_blinks=self.opt('cursor_blinks'),
            scrollback_lines=self.opt('scrollback_lines'),
            allow_bold = self.opt('allow_bold'),
            audible_bell = self.opt('audible_bell'),
        )
        if self.opt('use_background_image'):
            imagefile = self.opt('background_image_file')
            options['background_image_file'] = imagefile
        return options

    def set_current_project(self, project):
        self.current_project = project

    def get_current_project_directory(self):
        if self.current_project is not None:
            return self.current_project.source_directory
        else:
            return os.getcwd()

    def on_buffer_change(self, document):
        if not hasattr(self, '_terminals') or \
           not document.directory:
            # service not started yet
            # or new document
            return
        for term in self._terminals:
            if hasattr(term, '_stick_button') and \
               term._stick_button.child.get_active() and \
               term._term.window and \
               term._term.window.is_visible():
                term.chdir(document.directory)

    def list_matches(self):
        # we use this so the default matchers are always the latest
        # added to a terminal. this was the more specific ones are matching 
        # first
        rv = []
        for cmatch, ccall in self.features['matches']:
            rv.append(cmatch)
        return rv

    def get_match_callbacks(self, match):
        rv = []
        for cmatch, ccall in self.features['matches']:
            if match == cmatch:
                rv.append(ccall)
        return rv



# Required Service attribute for service loading
Service = Commander



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
