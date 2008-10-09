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
from pida.core.languages import (LanguageService, Outliner, Validator,
    Completer, LanguageServiceFeaturesConfig, LanguageInfo, PRIO_VERY_GOOD,
    PRIO_GOOD, Definer, Definition)

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

from ropebrowser import ModuleParser

class PythonEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                    self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_document(document)


class PythonFeaturesConfig(LanguageServiceFeaturesConfig):

    def subscribe_all_foreign(self):
        LanguageServiceFeaturesConfig.subscribe_all_foreign(self)
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

    def on_python_execute(self, action):
        self.svc.execute_current_document()


class PythonOutliner(Outliner):

    priority = PRIO_VERY_GOOD

    def get_outline(self):
        mp = ModuleParser(self.document.filename)
        for node, parent in mp.get_nodes():
            yield (node, parent)

class PythonLanguage(LanguageInfo):
    varchars = [chr(x) for x in xrange(97, 122)] + \
               [chr(x) for x in xrange(65, 90)] + \
               [chr(x) for x in xrange(48, 58)] + \
               ['_',]
    word = varchars

    # . in python
    attributerefs = ['.']


def _create_exception_validation(e):
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

class PythonValidator(Validator):

    priority = PRIO_GOOD

    def get_validations(self):
        code_string = self.document.content
        filename = self.document.filename
        try:
            tree = compiler.parse(code_string)
        except (SyntaxError, IndentationError), e:
            messages = _create_exception_validation(e)
        else:
            w = pyflakes.Checker(tree, filename)
            messages = w.messages
        for m in messages:
            yield m


class PythonCompleter(Completer):

    priority = PRIO_VERY_GOOD

    def get_completions(self, base, buffer, offset):
        mp = ModuleParser(self.document.filename)
        buffer = buffer + ('\n' * 20)

        from rope.contrib.codeassist import code_assist, sorted_proposals
        from rope.base.exceptions import RopeError
        
        try:
            co = code_assist(mp.project, buffer, offset)
        except RopeError:
            return []
        so = sorted_proposals(co)
        return [c.name for c in so if c.name.startswith(base)]


class PythonDefiner(Definer):

    def get_definition(self, buffer, offset):
        mp = ModuleParser(self.document.filename)
        buffer = buffer + ('\n' * 20)

        from rope.contrib.findit  import find_definition
        from rope.base.exceptions import RopeError

        try:
            dl = find_definition(mp.project, buffer, offset)
        except RopeError:
            return None

        if not dl:
            return None

        if dl.resource is not None:
            file_name = dl.resource.path
        else:
            file_name = self.document.filename


        rv = Definition(file_name=file_name, offset=dl.offset,
                        line=dl.lineno, length=(dl.region[1]-dl.region[0]))

        return rv


class Python(LanguageService):

    language_name = 'Python'
    language_info = PythonLanguage
    outliner_factory = PythonOutliner
    validator_factory = PythonValidator
    completer_factory = PythonCompleter
    definer_factory = PythonDefiner

    features_config = PythonFeaturesConfig
    actions_config = PythonActionsConfig
    options_config = PythonOptionsConfig
    events_config = PythonEventsConfig

    def pre_start(self):
        self.execute_action = self.get_action('execute_python')
        self.execute_action.set_sensitive(False)

    def execute_current_document(self):
        python_ex = self.opt('python_for_executing')
        self.boss.cmd('commander', 'execute',
            commandargs=[python_ex, self._current.filename],
            cwd = self._current.directory,
            )

    def is_current_python(self):
        t = self.boss.cmd('language', 'get_current_filetype')
        print t
        if t and (t.internal == self.language_name):
            return True
        return False

    def set_document(self, document):
        self.execute_action.set_sensitive(self.is_current_python())



# Required Service attribute for service loading
Service = Python



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
