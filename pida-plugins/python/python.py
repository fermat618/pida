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
import sys, compiler, os.path, keyword, re

# gtk
import gtk

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig
from pida.core.languages import (LanguageService, Outliner, Validator,
    Completer, LanguageServiceFeaturesConfig, LanguageInfo, Definer, 
    Documentator, External)

from pida.utils.languages import (LANG_COMPLETER_TYPES,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, LANG_OUTLINER_TYPES, 
    LANG_PRIO, Definition, Suggestion, Documentation, ValidationError)

# services
import pida.services.filemanager.filehiddencheck as filehiddencheck

# utils
from .pyflakes.checker import Checker
from . import pyflakes
from .pyflakes import messages
# locale
from pida.core.locale import Locale
locale = Locale('python')
_ = locale.gettext

from .ropebrowser import ModuleParser

MAX_FIXES = 10
RE_MATCHES = (
    # traceback match
    (r'''File\s*"([^"]+)",\s*line\s*[0-9]+''',
    # internal
     re.compile(r'\s*File\s*\"(?P<file>[^"]+)\",\s*line\s*(?P<line>\d+).*'))
    ,
    #FIXME: how to handle localisation of this ???
)


class PythonEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                    self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-typchanged',
                    self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_document(document)


class PythonFeaturesConfig(LanguageServiceFeaturesConfig):

    def subscribe_all_foreign(self):
        LanguageServiceFeaturesConfig.subscribe_all_foreign(self)
        self.subscribe_foreign('filemanager', 'file_hidden_check',
            self.python)
        for match in RE_MATCHES:
            self.subscribe_foreign('commander', 'match-callback',
            ('Python', match[0], match[1], self.svc.match_call))


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

    priority = LANG_PRIO.VERY_GOOD
    name = "rope"
    plugin = "python"
    description = _("A very deep and precises, but slow outliner")


    filter_type = (LANG_OUTLINER_TYPES.IMPORT,
                    LANG_OUTLINER_TYPES.BUILTIN,
                    LANG_OUTLINER_TYPES.METHOD,
                    LANG_OUTLINER_TYPES.FUNCTION,
                    LANG_OUTLINER_TYPES.PROPERTY,
                    LANG_OUTLINER_TYPES.ATTRIBUTE,
                    LANG_OUTLINER_TYPES.SUPERMETHOD,
                    )

    def get_outline(self):
        from rope.base.exceptions import RopeError
        try:
            mp = ModuleParser(self.document.filename,
                              project=self.document.project)
        except RopeError:
            return
        try:
            for node, parent in mp.get_nodes():
                yield node
        except Exception, e:
            import traceback
            traceback.print_exc()

    def sync(self):
        try:
            self.document.project['python']['ropeproject'].sync()
        except (KeyError, TypeError), e:
            pass

    def close(self):
        try:
            self.document.project['python']['ropeproject'].close()
        except (KeyError, TypeError), e:
            pass


class PythonDocumentator(Documentator):

    name = "rope"
    plugin = "python"
    description = _("A very good documentator")


    def get_documentation(self, buffer, offset):
        mp = ModuleParser(self.document.filename,
                          project=self.document.project)
        buffer = buffer + ('\n' * 20)
        
        from rope.contrib.codeassist import PyDocExtractor
        from rope.base.exceptions import RopeError
        from rope.contrib import fixsyntax
        try:
            fix = fixsyntax.FixSyntax(mp.project.pycore, buffer, None, maxfixes=MAX_FIXES)
            pymodule = fix.get_pymodule()
            pyname = fix.pyname_at(offset)
        except RopeError:
            return
        if pyname is None:
            return
        pyobject = pyname.get_object()
        rv = Documentation(
            short=PyDocExtractor().get_calltip(pyobject, False, False),
            long_=PyDocExtractor().get_doc(pyobject)
            )
        yield rv
        
class PythonLanguage(LanguageInfo):
    varchars = [chr(x) for x in xrange(97, 122)] + \
               [chr(x) for x in xrange(65, 90)] + \
               [chr(x) for x in xrange(48, 58)] + \
               ['_',]
    word = varchars

    # . in python
    attributerefs = ['.']

    completer_open = ['[', '(', ',', '.']
    completer_close = [']', ')', '}']



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
    msg.type_ = LANG_VALIDATOR_TYPES.ERROR
    if isinstance(e, SyntaxError):
        msg.subtype = LANG_VALIDATOR_SUBTYPES.SYNTAX
    else:
        msg.subtype = LANG_VALIDATOR_SUBTYPES.INDENTATION
    return [msg]

class PythonError(ValidationError):
    def get_markup(self):
        args = [('<b>%s</b>' % arg) for arg in self.message_args]
        message_string = self.message % tuple(args)
        if self.type_ == LANG_VALIDATOR_TYPES.ERROR:
            typec = self.lookup_color('pida-val-error')
        elif self.type_ == LANG_VALIDATOR_TYPES.INFO:
            typec = self.lookup_color('pida-val-info')
        elif self.type_ == LANG_VALIDATOR_TYPES.WARNING:
            typec = self.lookup_color('pida-val-warning')
        else:
            typec = self.lookup_color('pida-val-def')
        
        if typec:
            typec = typec.to_string()
        else:
            typec = "black"
        
        linecolor = self.lookup_color('pida-lineno')
        if linecolor:
            linecolor = linecolor.to_string()
        else:
            linecolor = "black"
        
        markup = ("""<tt><span color="%(linecolor)s">%(lineno)s</span> </tt>"""
    """<span foreground="%(typec)s" style="italic" weight="bold">%(type)s</span"""
    """>:<span style="italic">%(subtype)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno, 
                      'type':_(LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize()),
                      'subtype':_(LANG_VALIDATOR_SUBTYPES.whatis(
                                    self.subtype).capitalize()),
                      'message':message_string,
                      'linecolor': linecolor,
                      'typec': typec,
                      })
        return markup
    markup = property(get_markup)

class PythonValidator(Validator):

    priority = LANG_PRIO.GOOD
    name = "pyflakes"
    plugin = "python"
    description = _("A not very precise, non configurable validator, but fast")

    def get_validations(self):
        code_string = self.document.content
        filename = self.document.filename
        try:
            tree = compiler.parse(code_string)
        except (SyntaxError, IndentationError), e:
            messages = _create_exception_validation(e)
        else:
            w = Checker(tree, filename)
            messages = w.messages
        for m in messages:
            type_ = getattr(m, 'type_', LANG_VALIDATOR_TYPES.UNKNOWN)
            subtype = getattr(m, 'subtype', LANG_VALIDATOR_SUBTYPES.UNKNOWN)

            #FIXME add pyflakes 0.3 types
            #FIXME make mapping
            if isinstance(m, pyflakes.messages.UnusedImport):
                type_ = LANG_VALIDATOR_TYPES.INFO
                subtype = LANG_VALIDATOR_SUBTYPES.UNUSED
            elif isinstance(m, pyflakes.messages.RedefinedWhileUnused):
                type_ = LANG_VALIDATOR_TYPES.WARNING
                subtype = LANG_VALIDATOR_SUBTYPES.REDEFINED
            elif isinstance(m, pyflakes.messages.ImportStarUsed):
                type_ = LANG_VALIDATOR_TYPES.WARNING
                subtype = LANG_VALIDATOR_SUBTYPES.BADSTYLE
            elif isinstance(m, pyflakes.messages.UndefinedName):
                type_ = LANG_VALIDATOR_TYPES.ERROR
                subtype = LANG_VALIDATOR_SUBTYPES.UNDEFINED
            elif isinstance(m, pyflakes.messages.DuplicateArgument):
                type_ = LANG_VALIDATOR_TYPES.ERROR
                subtype = LANG_VALIDATOR_SUBTYPES.DUPLICATE

            ve = PythonError(
                message=m.message,
                message_args=m.message_args,
                lineno=m.lineno,
                type_=type_,
                subtype=subtype,
                filename=filename
                )
            yield ve


class PythonCompleter(Completer):

    priority = LANG_PRIO.VERY_GOOD
    name = "rope"
    plugin = "python"
    description = _("Creates very exact suggestions at reasonable speed")

    def get_completions(self, base, buffer, offset):

        from rope.contrib.codeassist import code_assist, sorted_proposals
        from rope.base.exceptions import RopeError

        try:
            mp = ModuleParser(self.document.filename, 
                              project=self.document.project)
            buffer = buffer + ('\n' * 20)
            co = code_assist(mp.project, buffer, offset, maxfixes=MAX_FIXES)
        except RopeError, IndentationError:
            return
        so = sorted_proposals(co)
        for c in so:
            if c.name.startswith(base):
                r = Suggestion(c.name)
                #'variable', 'class', 'function', 'imported' , 'paramter'
                if keyword.iskeyword(c.name):
                    r.type_ = LANG_COMPLETER_TYPES.KEYWORD
                elif c.type == 'variable':
                    r.type_ = LANG_COMPLETER_TYPES.VARIABLE
                elif c.type == 'class':
                    r.type_ = LANG_COMPLETER_TYPES.CLASS
                elif c.type == 'builtin':
                    r.type_ = LANG_COMPLETER_TYPES.BUILTIN
                elif c.type == 'function':
                    r.type_ = LANG_COMPLETER_TYPES.FUNCTION
                elif c.type == 'parameter':
                    r.type_ = LANG_COMPLETER_TYPES.PARAMETER
                elif c.type == None:
                    if c.kind == "parameter_keyword":
                        r.type_ = LANG_COMPLETER_TYPES.PARAMETER
                else:
                    r.type_ = LANG_COMPLETER_TYPES.UNKNOWN
                yield r

class PythonDefiner(Definer):

    name = "rope"
    plugin = "python"
    description = _("Shows a good definition of a function")

    def get_definition(self, buffer, offset):
        mp = ModuleParser(self.document.filename,
                          project=self.document.project)
        buffer = buffer + ('\n' * 20)

        from rope.contrib.findit  import find_definition
        from rope.base.exceptions import RopeError

        try:
            dl = find_definition(mp.project, buffer, offset, maxfixes=MAX_FIXES)
        except RopeError:
            return

        if not dl:
            return

        if dl.resource is not None:
            file_name = dl.resource.path
        else:
            file_name = self.document.filename


        rv = Definition(file_name=file_name, offset=dl.offset,
                        line=dl.lineno, length=(dl.region[1]-dl.region[0]))

        yield rv

class PythonExternal(External):
    outliner = PythonOutliner
    validator = PythonValidator
    completer = PythonCompleter
    definer = PythonDefiner
    documentator = PythonDocumentator

class Python(LanguageService):

    language_name = 'Python'
    language_info = PythonLanguage
    outliner_factory = PythonOutliner
    validator_factory = PythonValidator
    completer_factory = PythonCompleter
    definer_factory = PythonDefiner
    documentator_factory = PythonDocumentator

    features_config = PythonFeaturesConfig
    actions_config = PythonActionsConfig
    options_config = PythonOptionsConfig
    events_config = PythonEventsConfig

    external = PythonExternal

    def pre_start(self):
        self.execute_action = self.get_action('execute_python')
        self.execute_action.set_sensitive(False)

#     def start(self):
#         for match in RE_MATCHES:
#             self.boss.get_service('commander').register_matcher(
#                 match[0], self.match_call)
#
#     def stop(self):
#         for match in RE_MATCHES:
#             self.boss.get_service('commander').unregister_matcher(
#                 match[0], self.match_call)

    def match_call(self, term, event, match, *args, **kwargs):
        for pattern in RE_MATCHES:
            test = pattern[1].match(match)
            if test:
                self.boss.get_service('buffer').open_file(
                    kwargs['usr'].get_absolute_path(test.groups()[0]),
                    line=int(test.groups()[1]))

    def execute_current_document(self):
        python_ex = self.opt('python_for_executing')
        doc = self.boss.cmd('buffer', 'get_current')
        if doc and doc.filename:
            self.boss.cmd('commander', 'execute',
                commandargs=[python_ex, doc.filename],
                cwd = doc.directory,
                )

    def is_current_python(self):
        doc = self.boss.cmd('buffer', 'get_current')
        if doc.doctype and (doc.doctype.internal == self.language_name):
            return True
        return False

    def set_document(self, document):
        self.execute_action.set_sensitive(self.is_current_python())



# Required Service attribute for service loading
Service = Python



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

