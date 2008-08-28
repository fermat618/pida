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
import sys, compiler, os.path

# gtk
import gtk

# kiwi
from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig

# services
import pida.services.filemanager.filehiddencheck as filehiddencheck

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo

# utils
from . import pyflakes
from pida.utils.gthreads import AsyncTask, GeneratorTask

# locale
from pida.core.locale import Locale
locale = Locale('python')
_ = locale.gettext

### Pyflakes

class PyflakeView(PidaView):
    
    icon_name = 'python-icon'
    label_text = _('Python Errors')

    def create_ui(self):
        self.errors_ol = ObjectList(
            Column('markup', use_markup=True)
        )
        self.errors_ol.set_headers_visible(False)
        self.errors_ol.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_main_widget(self.errors_ol)
        self.errors_ol.connect('double-click', self._on_errors_double_clicked)
        self.errors_ol.show_all()
        self.sort_combo = AttrSortCombo(
            self.errors_ol,
            [
                ('lineno', _('Line Number')),
                ('message_string', _('Message')),
                ('name', _('Type')),
            ],
            'lineno',
        )
        self.sort_combo.show()
        self.add_main_widget(self.sort_combo, expand=False)

    def clear_items(self):
        self.errors_ol.clear()

    def set_items(self, items):
        self.clear_items()
        for item in items:
            self.errors_ol.append(self.decorate_pyflake_message(item))

    def decorate_pyflake_message(self, msg):
        args = [('<b>%s</b>' % arg) for arg in msg.message_args]
        msg.message_string = msg.message % tuple(args)
        msg.name = msg.__class__.__name__
        msg.markup = ('<tt>%s </tt><i>%s</i>\n%s' % 
                      (msg.lineno, msg.name, msg.message_string))
        return msg

    def _on_errors_double_clicked(self, ol, item):
        self.svc.boss.editor.cmd('goto_line', line=item.lineno)

    def can_be_closed(self):
        self.svc.get_action('show_python_errors').set_active(False)


class Pyflaker(object):

    def __init__(self, svc):
        self.svc = svc
        self._view = PyflakeView(self.svc)
        self.set_current_document(None)

    def set_current_document(self, document):
        self._current = document
        if self._current is not None:
            self.refresh_view()
            self._view.get_toplevel().set_sensitive(True)
        else:
            self.set_view_items([])
            self._view.get_toplevel().set_sensitive(False)

    def refresh_view(self):
        if self.svc.is_current_python():
            task = AsyncTask(self.check_current, self.set_view_items)
            task.start()
        else:
            self._view.clear_items()

    def check_current(self):
        return self.check(self._current)

    def check(self, document):
        code_string = document.content
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


class SourceView(PidaGladeView):

    gladefile = 'python-source-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Source')

    def create_ui(self):
        self.source_tree.set_columns(
            [
                #Column('linenumber'),
                #Column('ctype_markup', use_markup=True),
                #Column('nodename_markup', use_markup=True),
                Column('icon_name', use_stock=True),
                Column('rendered', use_markup=True, expand=True),
                Column('type_markup', use_markup=True),
                Column('sort_hack', visible=False),
                Column('line_sort_hack', visible=False),
            ]
        )
        self.source_tree.set_headers_visible(False)
        self.sort_box = AttrSortCombo(
            self.source_tree,
            [
                ('sort_hack', _('Alphabetical by type')),
                ('line_sort_hack', _('Line Number')),
                ('name', _('Name')),
            ],
            'sort_hack'
        )
        self.sort_box.show()
        self.main_vbox.pack_start(self.sort_box, expand=False)

    def clear_items(self):
        self.source_tree.clear()

    def add_node(self, node, parent):
        self.source_tree.append(parent, node)

    def can_be_closed(self):
        self.svc.get_action('show_python_source').set_active(False)

    def on_source_tree__double_click(self, tv, item):
        if item.linenumber is None:
            return
        if item.filename is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=item.filename)
        self.svc.boss.editor.cmd('goto_line', line=item.linenumber)
        self.svc.boss.editor.cmd('grab_focus')

    def on_show_super__toggled(self, but):
        self.browser.refresh_view()

    def on_show_builtins__toggled(self, but):
        self.browser.refresh_view()

    def on_show_imports__toggled(self, but):
        self.browser.refresh_view()



from ropebrowser import ModuleParser

class PythonBrowser(object):

    def __init__(self, svc):
        self.svc = svc
        self._view = SourceView(self.svc)
        # Naughty ali
        self._view.browser = self
        self.set_current_document(None)

    def set_current_document(self, document):
        self._current = document
        if self._current is not None:
            self.refresh_view()
            self._view.get_toplevel().set_sensitive(True)
        else:
            self._view.clear_items()
            self._view.get_toplevel().set_sensitive(False)

    def refresh_view(self):
        self.options = self.read_options()
        self._view.clear_items()
        if self.svc.is_current_python():
            task = GeneratorTask(self.check_current, self.add_view_node)
            task.start()

    def check_current(self):
        for node, parent in self.check(self._current):
            yield (node, parent)

    def check(self, document):
        mp = ModuleParser(document.filename)
        return mp.get_nodes()

    def add_view_node(self, node, parent):
        t = node.options.type_name
        if t in self.options and not self.options[t]:
            return
        self._view.add_node(node, parent)

    def get_view(self):
        return self._view

    def read_options(self):
        return {
            '(m)': self._view.show_super.get_active(),
            '(b)': self._view.show_builtins.get_active(),
            'imp': self._view.show_imports.get_active(),
        }


class PythonFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('filemanager', 'file_hidden_check',
            self.python)

    @filehiddencheck.fhc(filehiddencheck.SCOPE_PROJECT, 
        _("Hide Python Compiled Files"))
    def python(self, name, path, state):
        return os.path.splitext(name)[1] != '.pyc'

class PythonOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'python_for_executing',
            _('Python Executable for executing'),
            str,
            'python',
            _('The Python executable when executing a module'),
        )


class PythonEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed', self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-saved', self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_current_document(document)

class PythonActionsConfig(ActionsConfig):
    
    def create_actions(self):
        self.create_action(
            'execute_python',
            TYPE_NORMAL,
            _('Execute Python Module'),
            _('Execute the current Python module in a shell'),
            gtk.STOCK_EXECUTE,
            self.on_python_execute,
        )

        self.create_action(
            'show_python_errors',
            TYPE_TOGGLE,
            _('Python Error Viewer'),
            _('Show the python error browser'),
            'error',
            self.on_show_errors,
        )

        self.create_action(
            'show_python_source',
            TYPE_TOGGLE,
            _('Python Source Viewer'),
            _('Show the python source browser'),
            'info',
            self.on_show_source,
        )

    def on_python_execute(self, action):
        self.svc.execute_current_document()

    def on_show_errors(self, action):
        if action.get_active():
            self.svc.show_errors()
        else:
            self.svc.hide_errors()

    def on_show_source(self, action):
        if action.get_active():
            self.svc.show_source()
        else:
            self.svc.hide_source()


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
        self._pysource = PythonBrowser(self)
        self.execute_action = self.get_action('execute_python')
        self.execute_action.set_sensitive(False)

    def set_current_document(self, document):
        self._current = document
        if self.is_current_python():
            self._pyflaker.set_current_document(document)
            self._pysource.set_current_document(document)
            self.execute_action.set_sensitive(True)
        else:
            self._pyflaker.set_current_document(None)
            self._pysource.set_current_document(None)
            self.execute_action.set_sensitive(False)

    def is_current_python(self):
        if self._current is not None and self._current.filename:
            return self._current.filename.endswith('.py')
        else:
            return False

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

    def show_source(self):
        self.boss.cmd('window', 'add_view',
            paned='Plugin', view=self._pysource.get_view())

    def hide_source(self):
        self.boss.cmd('window', 'remove_view',
            view=self._pysource.get_view())

    def stop(self):
        if self.get_action('show_python_source').get_active():
            self.hide_source()
        if self.get_action('show_python_errors').get_active():
            self.hide_errors()
        del self._pysource
        del self._pyflaker

# Required Service attribute for service loading
Service = Python



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
