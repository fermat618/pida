# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import sys
import pango
import gtk

from pida.utils import ostools
# PIDA Imports
import pida
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig



# locale
from pida.core.locale import Locale
locale = Locale('commander')
_ = locale.gettext


from .views import TerminalView, PythonView

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
            gtk.Action,
            _('_Run Shell'),
            _('Open a shell prompt'),
            'terminal',
            self.execute_shell,
            '<Shift><Control>T',
        )

        self.create_action(
            'python_shell',
            gtk.Action,
            _('_Run Python Shell'),
            _('Open a python shell'),
            'terminal',
            self.execute_python_shell,
            '<Shift><Control>P',
        )

        self.create_action(
            'terminal-for-file',
            gtk.Action,
            _('Shell in file directory'),
            _('Open a shell prompt in the parent directory of this file'),
            'terminal',
            self.on_terminal_for_file,
        )

        self.create_action(
            'terminal-for-dir',
            gtk.Action,
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

    def execute(self, commandargs, env=(), cwd=os.getcwd(), title=_('Command'),
                      icon='terminal', eof_handler=None, use_python_fork=False,
                      parser_func=None):
        return self.svc.execute(commandargs, env, cwd, title, icon,
                                eof_handler, use_python_fork, parser_func)

    def execute_shell(self, env=(), cwd=os.getcwd(), title='Shell'):
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
        env_pida = list(env)
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
