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

# stdlib
import sys, compiler

# gtk
import gtk

# kiwi
from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE
from pida.core.options import OptionsConfig, OTypeString
from pida.core.features import FeaturesConfig
from pida.core.projects import ProjectController, project_action,\
    BuildActionType, ExecutionActionType, TestActionType
from pida.core.interfaces import IProjectController

# ui
from pida.ui.views import PidaView

# utils
from pida.utils import pyflakes
from pida.utils.gthreads import AsyncTask, gcall

### Pyflakes

class PyflakeView(PidaView):
    
    icon_name = 'info'
    label_text = 'Python Errors'

    def create_ui(self):
        self.errors_ol = ObjectList(
            Column('markup', use_markup=True)
        )
        self.errors_ol.set_headers_visible(False)
        self.errors_ol.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_main_widget(self.errors_ol)
        self.errors_ol.connect('double-click', self._on_errors_double_clicked)
        self.errors_ol.show_all()

    def clear_items(self):
        self.errors_ol.clear()

    def set_items(self, items):
        self.clear_items()
        for item in items:
            self.errors_ol.append(self.decorate_pyflake_message(item))

    def decorate_pyflake_message(self, msg):
        args = [('<b>%s</b>' % arg) for arg in msg.message_args]
        message_string = msg.message % tuple(args)
        msg.markup = ('<tt>%s </tt><i>%s</i>\n%s' % 
                      (msg.lineno, msg.__class__.__name__, message_string))
        return msg

    def _on_errors_double_clicked(self, ol, item):
        self.svc.boss.cmd('vim', 'goto_line', line=item.lineno)

class Pyflaker(object):

    def __init__(self, svc):
        self.svc = svc
        self._view = PyflakeView(self.svc)

    def set_current_document(self, document):
        self._current = document
        self.refresh_view()

    def refresh_view(self):
        if self.svc.is_current_python():
            task = AsyncTask(self.check_current, self.set_view_items)
            task.start()
        else:
            self._view.clear_items()

    def check_current(self):
        return self.check(self._current)

    def check(self, document):
        code_string = document.string
        filename = document.filename
        try:
            tree = compiler.parse(code_string)
        except (SyntaxError, IndentationError), e:
            msg = e
            msg.name = e.__class__.__name__
            value = sys.exc_info()[1]
            (lineno, offset, line) = value[1][1:]
            if line.endswith("\n"):
                line = line[:-1]
            msg.lineno = lineno
            msg.message_args = (line,)
            msg.message = '<tt>%%s</tt>\n<tt>%s^</tt>' % (' ' * (offset - 2))
            return [msg]
        else:
            w = pyflakes.Checker(tree, filename)
            return w.messages

    def set_view_items(self, items):
        self._view.set_items(items)


    def get_view(self):
        return self._view
        

class PythonProjectController(ProjectController):

    name = 'PYTHON_CONTROLLER'

    @project_action(kind=BuildActionType)
    def build(self):
        self.execute_commandargs(
            [self.get_python_executable(), 'setup.py', 'build'],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    @project_action(kind=TestActionType)
    def test(self):
        self.execute_commandargs(
            [self.get_option('test_command')],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandargs(
            [self.get_python_executable(), self.get_option('execute_file')],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    def get_python_executable(self):
        return self.get_option('python_executable') or 'python'

class PythonFeatures(FeaturesConfig):

    def subscribe_foreign_features(self):
        self.subscribe_foreign_feature('project', IProjectController,
            PythonProjectController)


class PythonOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'python_for_executing',
            'Python Executable for executing',
            OTypeString,
            'python',
            'The Python executable when executing a module',
        )


class PythonEventsConfig(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed', self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_current_document(document)

class PythonActionsConfig(ActionsConfig):
    
    def create_actions(self):
        self.create_action(
            'execute_python',
            TYPE_NORMAL,
            'Execute Python Module',
            'Execute the current Python module in a shell',
            gtk.STOCK_EXECUTE,
            self.on_python_execute,
        )

        self.create_action(
            'show_python_errors',
            TYPE_TOGGLE,
            'Python Errors',
            'Show the python error browser',
            'info',
            self.on_show_errors,
        )

    def on_python_execute(self, action):
        self.svc.execute_current_document()

    def on_show_errors(self, action):
        if action.get_active():
            self.svc.show_errors()
        else:
            self.svc.hide_errors()

# Service class
class Python(Service):
    """Service for all things Python""" 

    events_config = PythonEventsConfig
    actions_config = PythonActionsConfig
    options_config = PythonOptionsConfig
    features_config = PythonFeatures

    def pre_start(self):
        """Start the service"""
        self._current = None
        self._pyflaker = Pyflaker(self)
        self.execute_action = self.get_action('execute_python')
        self.execute_action.set_sensitive(False)

    def set_current_document(self, document):
        self._current = document
        self._pyflaker.set_current_document(document)
        self.execute_action.set_sensitive(self.is_current_python())

    def is_current_python(self):
        return self._current.filename.endswith('.py')

    def execute_current_document(self):
        python_ex = self.opt('python_for_executing')
        self.boss.cmd('commander', 'execute',
            commandargs=[python_ex, self._current.filename],
            cwd = self._current.directory,
            )

    def show_errors(self):
        self.boss.cmd('window', 'add_view',
            paned='Plugin', view=self._pyflaker.get_view())

    def hide_errors(self):
        self.boss.cmd('window', 'remove_view',
            view=self._pyflaker.get_view())

# Required Service attribute for service loading
Service = Python



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
