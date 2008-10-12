# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import os, subprocess

import gtk
import gtk.gdk
import gobject
import pango

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida import PIDA_VERSION

from pida.utils.gthreads import AsyncTask

from pida.ui.views import PidaView
from pida.ui.terminal import PidaTerminal
from pida.ui.buttons import create_mini_button

# locale
from pida.core.locale import Locale
locale = Locale('commander')
_ = locale.gettext


#RE_ABSOLUTE_UNIX = r'^((?:\/[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*(?:\-[a-zA-Z0-9]+)*)+)$'
#RE_ABSOLUTE_UNIX = r'''((?:\.\./|[a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(?:\:[1-9]+)?)'''
#RE_ABSOLUTE_UNIX = r'((\.\./|[a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(?:\:\d+)?)'

RE_MATCHES = (r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(\:[0-9]+)?)',
              r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+)'
             )

def get_default_system_shell():
    return os.environ.get('SHELL', 'bash')

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
            get_default_system_shell(),
            _('The command that will be used for shells')
        )

        self.create_option(
            'shell_command_args',
            _('The shell arguments'),
            list,
            [],
            _('The arguments to pass to the shell command'),
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

    def on_terminal_for_file(self, action):
        cwd = os.path.dirname(action.contexts_kw['file_name'])
        self.svc.cmd('execute_shell', cwd=cwd)

    def on_terminal_for_dir(self, action):
        cwd = action.contexts_kw['dir_name']
        self.svc .cmd('execute_shell', cwd=cwd)


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

class CommanderFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc.get_action_group(), 'commander-file-menu.xml'))
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc.get_action_group(), 'commander-dir-menu.xml'))

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
        self._pwd = None
        self._pid = None
        self._hb = gtk.HBox()
        self._hb.show()
        self.add_main_widget(self._hb)
        self._term = PidaTerminal(**self.svc.get_terminal_options())
        for match in RE_MATCHES:
            i = self._term.match_add(match)
            self._term.match_set_cursor_type(i, gtk.gdk.HAND2)
        self._term.parent_view = self
        self._term.connect('window-title-changed', self.on_window_title_changed)
        self._term.connect('selection-changed', self.on_selection_changed)
        self._term.connect('button_press_event', self.on_button_pressed)
        self._term.show()
        self._create_scrollbar()
        self._create_bar()
        self._hb.pack_start(self._term)
        if self.svc.opt('scrollbar_visible'):
            self._hb.pack_start(self._scrollbar, expand=False)
        self._hb.pack_start(self._bar, expand=False)
        self.master = None
        self.slave = None
        self.prep_highlights()

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
        self._title.set_text(title_text)
        if eof_handler is None:
            eof_handler = self.on_exited
        self.eof_handler = eof_handler
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
        gobject.io_add_watch(self.master, gobject.IO_IN, 
                                self._on_python_fork_parse_stdout, parser_func)
        self._term.connect('key-press-event',
                            self._on_python_fork_parse_key_press_event, self.master)

    def _on_python_fork_parse_key_press_event(self, term, event, fd):
        if event.hardware_keycode == 22:
            os.write(fd, "")
        elif event.hardware_keycode == 98:
            os.write(fd, "OA")
        elif event.hardware_keycode == 104:
            os.write(fd, "OB")
        elif event.hardware_keycode == 100:
            os.write(fd, "OD")
        elif event.hardware_keycode == 102:
            os.write(fd, "OC")
        else:
            data = event.string
            os.write(fd, data)
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

    def close_view(self):
        self.svc.boss.cmd('window', 'remove_view', view=self)

    def on_exited(self, term):
        self._term.feed_text(_('Child exited')+'\r\n', '1;34')
        self._term.feed_text(_('Press any key to close.'))
        self._term.connect('commit', self.on_press_any_key)

    def can_be_closed(self):
        self.kill()
        return True

    def kill(self):
        if self._pid is not None:
            try:
                os.kill(self._pid, 9)
            except OSError:
                self.svc.log_debug('PID %s has already gone' % self._pid)

    def on_button_pressed(self, term, event):
        if not event.button in [1,2] or \
           not event.state & gtk.gdk.CONTROL_MASK:
            return
        line = int(event.y/self._term.get_char_height())
        col = int(event.x/self._term.get_char_width())
        match = self._term.match_check(col, line)
        if match:
            match = os.path.expanduser(match[0])
            if match.find(":") != -1:
                
                file_name, line = match.rsplit(":", 1)
                if os.path.isfile(file_name):
                    self.svc.boss.cmd('buffer', 'open_file', file_name=file_name,
                                         line=int(line))
                else:
                    self.svc.boss.cmd('filemanager', 'browse', new_path=file_name)
                    self.svc.boss.cmd('filemanager', 'present_view')
                    
            else:
                if os.path.isfile(match):
                    self.svc.boss.cmd('buffer', 'open_file', file_name=match)
                else:
                    self.svc.boss.cmd('filemanager', 'browse', new_path=match)
                    self.svc.boss.cmd('filemanager', 'present_view')

    def on_selection_changed(self, term):
        self._copy_button.set_sensitive(self._term.get_has_selection())

    def on_copy_clicked(self, button):
        self._term.copy_clipboard()

    def on_paste_clicked(self, button):
        self._term.paste_clipboard()

    def on_press_any_key(self, term, data, datalen):
        self.close_view()

    def on_commit_python(self, term, data, datalen):
        if data == '\x03':
            os.kill(self._pid, 2)

    def on_window_title_changed(self, term):
        self._title.set_text(term.get_window_title())

    def prep_highlights(self):
        self._term.match_add_menu_callback('url-match',
            r'https{0,1}://[A-Za-z0-9/\-\._]+',
            r'(https{0,1}://[A-Za-z0-9/\-\._]+)',
            self.on_highlight_url)
        self._term.match_add_menu_callback('dir-match',
            r'~{0,1}/[a-zA-Z/\-\._]+',
            r'(~{0,1}/[A-Za-z0-9/\-\._]+)',
            self.on_highlight_path)

    def on_highlight_path(self, path, *args, **kw):
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return self.svc.boss.cmd('contexts', 'get_menu', context='dir-menu',
                                     dir_name=path)
        elif os.path.isfile(path):
            return self.svc.boss.cmd('contexts', 'get_menu', context='file-menu',
                                     file_name=path)
        else:
            return None

    def on_highlight_url(self, url, *args, **kw):
        return self.svc.boss.cmd('contexts', 'get_menu', context='url-menu',
                                  url=url)
    
    def chdir(self, path):
        # here we could look at the environment var to find out the real 
        # directory
        if self._pwd == path:
            return
        # maybe we find a good way to check if the term is currently
        # in shell mode and maybe there is a better way to change
        # directories somehow
        # this is like kate does it
        self._term.feed_child(u'cd %s\n' %path)
        self._pwd = path

# Service class
class Commander(Service):
    """Describe your Service Here""" 

    commands_config = CommanderCommandsConfig
    actions_config = CommanderActionsConfig
    options_config = CommanderOptionsConfig
    features_config = CommanderFeaturesConfig
    events_config = CommanderEvents

    def start(self):
        self._terminals = []
        self.current_project = None

    def execute(self, commandargs, env, cwd, title, icon, eof_handler=None,
                use_python_fork=False, parser_func=None):
        env_pida = env
        env_pida.append('PIDA_VERSION=%s' % PIDA_VERSION)
        current_project = self.boss.cmd('project', 'get_current_project')
        if current_project:
            env_pida.append('PIDA_PROJECT=%s' % current_project.source_directory)
        t = TerminalView(self, title, icon)
        t.execute(commandargs, env_pida, cwd, eof_handler, use_python_fork, parser_func)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=t)
        self._terminals.append(t)
        return t

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
            if term._stick_button.child.get_active() and \
               term._term.window.is_visible():
                term.chdir(document.directory)


# Required Service attribute for service loading
Service = Commander



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
