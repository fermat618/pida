# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

"""
    pida.services.languages
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies support for languages


    :license: GPL2 or later
"""

import gtk
import pida.plugins

from kiwi.ui.objectlist import Column
from kiwi.ui.objectlist import ObjectList


from pida.core.environment import plugins_dir

from pida.core.doctype import TypeManager
from pida.utils.pdbus import EXPORT

from pida.utils.gthreads import GeneratorTask


# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo


# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

def get_value(tab, key):
    return tab.get(key, None)



class ValidatorView(PidaView):

    icon_name = 'python-icon'
    label_text = _('Language Errors')

    def set_validator(self, validator):
        self.clear_nodes()
        task = GeneratorTask(validator.get_validations, self.add_node)
        task.start()

    def add_node(self, node):
        self.errors_ol.append(self.decorate_pyflake_message(node))

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

    def clear_nodes(self):
        self.errors_ol.clear()

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
        return True
        # FIXME
        #self.svc.get_action('show_python_errors').set_active(False)


class BrowserView(PidaGladeView):

    gladefile = 'outline-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Outliner')

    def create_ui(self):
        self.source_tree.set_columns(
            [
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

    def set_outliner(self, outliner):
        self.clear_items()
        self.options = self.read_options()
        task = GeneratorTask(outliner.get_outline, self.add_node)
        task.start()

    def clear_items(self):
        self.source_tree.clear()

    def add_node(self, node, parent):
        self.source_tree.append(parent, node)

    def can_be_closed(self):
        self.svc.get_action('show_outliner').set_active(False)

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

    def read_options(self):
        return {
            '(m)': self.show_super.get_active(),
            '(b)': self.show_builtins.get_active(),
            'imp': self.show_imports.get_active(),
        }


class LanguageActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_validator',
            TYPE_TOGGLE,
            _('Validator'),
            _('Show the language validator'),
            'error',
            self.on_show_validator,
        )

        self.create_action(
            'show_browser',
            TYPE_TOGGLE,
            _('Outliner'),
            _('Show the language browser'),
            'info',
            self.on_show_browser,
        )

    def on_show_validator(self, action):
        if action.get_active():
            self.svc.show_validator()
        else:
            self.svc.hide_validator()

    def on_show_browser(self, action):
        if action.get_active():
            self.svc.show_browser()
        else:
            self.svc.hide_browser()


class LanguageCommandsConfig(CommandsConfig):

    # Are either of these commands necessary?

    def get_current_filetype(self):
        return self.svc.current_type

    def present_validator_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_validator())

    def present_browser_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_browser())


class LanguageOptionsConfig(OptionsConfig):
    pass
    #def create_options(self):
    #    self.create_option(
    #        'autoload',
    #        _('Autoload language support'),
    #        bool,
    #        True,
    #        _('Automaticly load language support on opening files'))


class LanguageFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        pass


class LanguageEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed', self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-saved', self.on_document_changed)

    def create(self):
        self.publish('plugin_started', 'plugin_stopped')

    def on_document_changed(self, document):
        self.svc.on_buffer_changed(document)



#taken from pygments _mappings.py

_DEFMAPPING = {
    'ActionScript': ('ActionScript', ('as', 'actionscript'), ('*.as',), ('application/x-actionscript', 'text/x-actionscript', 'text/actionscript')),
    'ApacheConf': ('ApacheConf', ('apacheconf', 'aconf', 'apache'), ('.htaccess', 'apache.conf', 'apache2.conf'), ('text/x-apacheconf',)),
    'BBCode': ('BBCode', ('bbcode',), (), ('text/x-bbcode',)),
    'Bash': ('Bash', ('bash', 'sh'), ('*.sh',), ('application/x-sh', 'application/x-shellscript')),
    'Batch': ('Batchfile', ('bat',), ('*.bat', '*.cmd'), ('application/x-dos-batch',)),
    'Befunge': ('Befunge', ('befunge',), ('*.befunge',), ('application/x-befunge',)),
    'Boo': ('Boo', ('boo',), ('*.boo',), ('text/x-boo',)),
    'Brainfuck': ('Brainfuck', ('brainfuck', 'bf'), ('*.bf', '*.b'), ('application/x-brainfuck',)),
    'C': ('C', ('c',), ('*.c', '*.h'), ('text/x-chdr', 'text/x-csrc')),
    'CObjdump': ('c-objdump', ('c-objdump',), ('*.c-objdump',), ('text/x-c-objdump',)),
    'CSharp': ('C#', ('csharp', 'c#'), ('*.cs',), ('text/x-csharp',)),
    'CommonLisp': ('Common Lisp', ('common-lisp', 'cl'), ('*.cl', '*.lisp', '*.el'), ('text/x-common-lisp',)),
    'Cpp': ('C++', ('cpp', 'c++'), ('*.cpp', '*.hpp', '*.c++', '*.h++'), ('text/x-c++hdr', 'text/x-c++src')),
    'CppObjdump': ('cpp-objdump', ('cpp-objdump', 'c++-objdumb', 'cxx-objdump'), ('*.cpp-objdump', '*.c++-objdump', '*.cxx-objdump'), ('text/x-cpp-objdump',)),
    'CssDjango': ('CSS+Django/Jinja', ('css+django', 'css+jinja'), (), ('text/css+django', 'text/css+jinja')),
    'CssErb': ('CSS+Ruby', ('css+erb', 'css+ruby'), (), ('text/css+ruby',)),
    'CssGenshi': ('CSS+Genshi Text', ('css+genshitext', 'css+genshi'), (), ('text/css+genshi',)),
    'Css': ('CSS', ('css',), ('*.css',), ('text/css',)),
    'CssPhp': ('CSS+PHP', ('css+php',), (), ('text/css+php',)),
    'CssSmarty': ('CSS+Smarty', ('css+smarty',), (), ('text/css+smarty',)),
    'D': ('D', ('d',), ('*.d', '*.di'), ('text/x-dsrc',)),
    'DObjdump': ('d-objdump', ('d-objdump',), ('*.d-objdump',), ('text/x-d-objdump',)),
    'DebianControl': ('Debian Control file', ('control',), ('control',), ()),
    'Delphi': ('Delphi', ('delphi', 'pas', 'pascal', 'objectpascal'), ('*.pas',), ('text/x-pascal',)),
    'Diff': ('Diff', ('diff',), ('*.diff', '*.patch'), ('text/x-diff', 'text/x-patch')),
    'Django': ('Django/Jinja', ('django', 'jinja'), (), ('application/x-django-templating', 'application/x-jinja')),
    'Dylan': ('Dylan', ('dylan',), ('*.dylan',), ('text/x-dylan',)),
    'Erb': ('ERB', ('erb',), (), ('application/x-ruby-templating',)),
    'Erlang': ('Erlang', ('erlang',), ('*.erl', '*.hrl'), ('text/x-erlang',)),
    'Gas': ('GAS', ('gas',), ('*.s', '*.S'), ('text/x-gas',)),
    'Genshi': ('Genshi', ('genshi', 'kid', 'xml+genshi', 'xml+kid'), ('*.kid',), ('application/x-genshi', 'application/x-kid')),
    'GenshiText': ('Genshi Text', ('genshitext',), (), ('application/x-genshi-text', 'text/x-genshi')),
    'Gettext': ('Gettext Catalog', ('pot', 'po'), ('*.pot', '*.po'), ('application/x-gettext', 'text/x-gettext', 'text/gettext')),
    'Groff': ('Groff', ('groff', 'nroff', 'man'), ('*.[1234567]', '*.man'), ('application/x-troff', 'text/troff')),
    'Haskell': ('Haskell', ('haskell', 'hs'), ('*.hs',), ('text/x-haskell',)),
    'HtmlDjango': ('HTML+Django/Jinja', ('html+django', 'html+jinja'), (), ('text/html+django', 'text/html+jinja')),
    'HtmlGenshi': ('HTML+Genshi', ('html+genshi', 'html+kid'), (), ('text/html+genshi',)),
    'Html': ('HTML', ('html',), ('*.html', '*.htm', '*.xhtml', '*.xslt'), ('text/html', 'application/xhtml+xml')),
    'HtmlPhp': ('HTML+PHP', ('html+php',), ('*.phtml',), ('application/x-php', 'application/x-httpd-php', 'application/x-httpd-php3', 'application/x-httpd-php4', 'application/x-httpd-php5')),
    'HtmlSmarty': ('HTML+Smarty', ('html+smarty',), (), ('text/html+smarty',)),
    'Ini': ('INI', ('ini', 'cfg'), ('*.ini', '*.cfg'), ('text/x-ini',)),
    'IrcLogs': ('IRC logs', ('irc',), ('*.weechatlog',), ('text/x-irclog',)),
    'Java': ('Java', ('java',), ('*.java',), ('text/x-java',)),
    'JavascriptDjango': ('JavaScript+Django/Jinja', ('js+django', 'javascript+django', 'js+jinja', 'javascript+jinja'), (), ('application/x-javascript+django', 'application/x-javascript+jinja', 'text/x-javascript+django', 'text/x-javascript+jinja', 'text/javascript+django', 'text/javascript+jinja')),
    'JavascriptErb': ('JavaScript+Ruby', ('js+erb', 'javascript+erb', 'js+ruby', 'javascript+ruby'), (), ('application/x-javascript+ruby', 'text/x-javascript+ruby', 'text/javascript+ruby')),
    'JavascriptGenshi': ('JavaScript+Genshi Text', ('js+genshitext', 'js+genshi', 'javascript+genshitext', 'javascript+genshi'), (), ('application/x-javascript+genshi', 'text/x-javascript+genshi', 'text/javascript+genshi')),
    'Javascript': ('JavaScript', ('js', 'javascript'), ('*.js',), ('application/x-javascript', 'text/x-javascript', 'text/javascript')),
    'JavascriptPhp': ('JavaScript+PHP', ('js+php', 'javascript+php'), (), ('application/x-javascript+php', 'text/x-javascript+php', 'text/javascript+php')),
    'JavascriptSmarty': ('JavaScript+Smarty', ('js+smarty', 'javascript+smarty'), (), ('application/x-javascript+smarty', 'text/x-javascript+smarty', 'text/javascript+smarty')),
    'Jsp': ('Java Server Page', ('jsp',), ('*.jsp',), ('application/x-jsp',)),
    'LiterateHaskell': ('Literate Haskell', ('lhs', 'literate-haskell'), ('*.lhs',), ('text/x-literate-haskell',)),
    'Llvm': ('LLVM', ('llvm',), ('*.ll',), ('text/x-llvm',)),
    'Lua': ('Lua', ('lua',), ('*.lua',), ('text/x-lua', 'application/x-lua')),
    'MOOCode': ('MOOCode', ('moocode',), ('*.moo',), ('text/x-moocode',)),
    'Makefile': ('Makefile', ('make', 'makefile', 'mf'), ('*.mak', 'Makefile', 'makefile'), ('text/x-makefile',)),
    'MakoCss': ('CSS+Mako', ('css+mako',), (), ('text/css+mako',)),
    'MakoHtml': ('HTML+Mako', ('html+mako',), (), ('text/html+mako',)),
    'MakoJavascript': ('JavaScript+Mako', ('js+mako', 'javascript+mako'), (), ('application/x-javascript+mako', 'text/x-javascript+mako', 'text/javascript+mako')),
    'Mako': ('Mako', ('mako',), ('*.mao',), ('application/x-mako',)),
    'MakoXml': ('XML+Mako', ('xml+mako',), (), ('application/xml+mako',)),
    'MiniD': ('MiniD', ('minid',), ('*.md',), ('text/x-minidsrc',)),
    'MoinWiki': ('MoinMoin/Trac Wiki markup', ('trac-wiki', 'moin'), (), ('text/x-trac-wiki',)),
    'MuPAD': ('pygments.s.math', 'MuPAD', ('mupad',), ('*.mu',), ()),
    'MySql': ('MySQL', ('mysql',), (), ('text/x-mysql',)),
    'MyghtyCss': ('CSS+Myghty', ('css+myghty',), (), ('text/css+myghty',)),
    'MyghtyHtml': ('HTML+Myghty', ('html+myghty',), (), ('text/html+myghty',)),
    'MyghtyJavascript': ('JavaScript+Myghty', ('js+myghty', 'javascript+myghty'), (), ('application/x-javascript+myghty', 'text/x-javascript+myghty', 'text/javascript+mygthy')),
    'Myghty': ('Myghty', ('myghty',), ('*.myt', 'autodelegate'), ('application/x-myghty',)),
    'MyghtyXml': ('XML+Myghty', ('xml+myghty',), (), ('application/xml+myghty',)),
    'Objdump': ('objdump', ('objdump',), ('*.objdump',), ('text/x-objdump',)),
    'ObjectiveC': ('Objective-C', ('objective-c', 'objectivec', 'obj-c', 'objc'), ('*.m',), ('text/x-objective-c',)),
    'Ocaml': ('OCaml', ('ocaml',), ('*.ml', '*.mli', '*.mll', '*.mly'), ('text/x-ocaml',)),
    'Perl': ('Perl', ('perl', 'pl'), ('*.pl', '*.pm'), ('text/x-perl', 'application/x-perl')),
    'Php': ('PHP', ('php', 'php3', 'php4', 'php5'), ('*.php', '*.php[345]'), ('text/x-php',)),
    'PythonConsole': ('Python console session', ('pycon',), (), ('text/x-python-doctest',)),
    'Python': ('Python', ('python', 'py'), ('*.py', '*.pyw', '*.sc', 'SConstruct', 'SConscript'), ('text/x-python', 'application/x-python')),
    'PythonTraceback': ('Python Traceback', ('pytb',), ('*.pytb',), ('text/x-python-traceback',)),
    'RawToken': ('Raw token data', ('raw',), ('*.raw',), ('application/x-pygments-tokens',)),
    'Redcode': ('Redcode', ('redcode',), ('*.cw',), ()),
    'Rhtml': ('RHTML', ('rhtml', 'html+erb', 'html+ruby'), ('*.rhtml',), ('text/html+ruby',)),
    'Rst': ('reStructuredText', ('rst', 'rest', 'restructuredtext'), ('*.rst', '*.rest'), ('text/x-rst',)),
    'RubyConsole': ('Ruby irb session', ('rbcon', 'irb'), (), ('text/x-ruby-shellsession',)),
    'Ruby': ('Ruby', ('rb', 'ruby'), ('*.rb', '*.rbw', 'Rakefile', '*.rake', '*.gemspec', '*.rbx'), ('text/x-ruby', 'application/x-ruby')),
    'Scheme': ('Scheme', ('scheme', 'scm'), ('*.scm',), ('text/x-scheme', 'application/x-scheme')),
    'Smarty': ('Smarty', ('smarty',), ('*.tpl',), ('application/x-smarty',)),
    'SourcesList': ('Debian Sourcelist', ('sourceslist', 'sources.list'), ('sources.list',), ()),
    'Sql': ('SQL', ('sql',), ('*.sql',), ('text/x-sql',)),
    'SquidConf': ('SquidConf', ('squidconf', 'squid.conf', 'squid'), ('squid.conf',), ('text/x-squidconf',)),
    'Tex': ('TeX', ('tex', 'latex'), ('*.tex', '*.aux', '*.toc'), ('text/x-tex', 'text/x-latex')),
    'Text': ('Text only', ('text',), ('*.txt',), ('text/plain',)),
    'VbNet': ('VB.net', ('vb.net', 'vbnet'), ('*.vb', '*.bas'), ('text/x-vbnet', 'text/x-vba')),
    'Vim': ('VimL', ('vim',), ('*.vim', '.vimrc'), ('text/x-vim',)),
    'XmlDjango': ('XML+Django/Jinja', ('xml+django', 'xml+jinja'), (), ('application/xml+django', 'application/xml+jinja')),
    'XmlErb': ('XML+Ruby', ('xml+erb', 'xml+ruby'), (), ('application/xml+ruby',)),
    'Xml': ('XML', ('xml',), ('*.xml', '*.xsl', '*.rss', '*.xslt'), ('text/xml', 'application/xml', 'image/svg+xml', 'application/rss+xml', 'application/atom+xml', 'application/xsl+xml', 'application/xslt+xml')),
    'XmlPhp': ('XML+PHP', ('xml+php',), (), ('application/xml+php',)),
    'XmlSmarty': ('XML+Smarty', ('xml+smarty',), (), ('application/xml+smarty',))
}

class LanguageDbusConfig(DbusConfig):

    @EXPORT(out_signature = 'as', in_signature = 'si')
    def get_completions(self, buffer, offset):
        print len(buffer), offset
        print [self.svc.current_completer]
        if self.svc.current_completer is not None:
            return self.svc.current_completer.get_completions(buffer, offset)
        else:
            return []


class Language(Service):
    """ Language manager service """

    actions_config = LanguageActionsConfig
    options_config = LanguageOptionsConfig
    events_config = LanguageEvents
    features_config = LanguageFeatures
    commands_config = LanguageCommandsConfig
    dbus_config = LanguageDbusConfig

    def pre_start(self):
        self.doctypes = TypeManager()
        self.doctypes._parse_map(_DEFMAPPING)
        self._view_outliner = BrowserView(self)
        self._view_validator = ValidatorView(self)
        self.current_type = None
        self.current_completer = None

    def show_validator(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_validator)

    def hide_validator(self):
        self.boss.cmd('window', 'remove_view', view=self._view_validator)

    def show_browser(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_outliner)

    def hide_browser(self):
        self.boss.cmd('window', 'remove_view', view=self._view_outliner)

    def on_buffer_changed(self, document):
        doctypes = self.doctypes.types_by_filename(document.filename)
        if not doctypes:
            self.current_type = None
            return
        type = doctypes[0]
        self.current_type = doctypes[0]
        outliners = self.features[(type.internal, 'outliner')]
        if outliners:
            outliner = list(outliners)[0]
            outliner.set_document(document)
            self._view_outliner.set_outliner(outliner)

        validators = self.features[(type.internal, 'validator')]
        if validators:
            validator = list(validators)[0]
            validator.set_document(document)
            self._view_validator.set_validator(validator)

        completers = self.features[(type.internal, 'completer')]
        if completers:
            completer = list(completers)[0]
            completer.set_document(document)
            self.current_completer = completer
        else:
            self.current_completer = None


    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)




Service = Language

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
