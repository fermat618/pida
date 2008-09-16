# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.doctype
    ~~~~~~~~~~~~~~~~~~

    :license: GPL3 or later
    :copyright:
        * 2008 Daniel Poelzleithner
"""

from glob import fnmatch

# taken from pygments _mappings.py

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


PRIO_PERFECT = 100
PRIO_VERY_GOOD = 50
PRIO_GOOD = 10
PRIO_DEFAULT = 0
PRIO_LOW = -50
PRIO_BAD = -100

class DocType(object):
    """Represents a type of document. Like a python sourcecode file, a xml
    file, etc.
    """
    __slots__ = ('internal', 'aliases', 'human', 'extensions', 'mimes', 
                 'parsers', 'validators')

    def __init__(self, internal, human, aliases = None, extensions = None, mimes = None):
        self.internal = internal
        self.human = human
        self.aliases = aliases and list(aliases) or []
        self.extensions = extensions and list(extensions) or []
        self.mimes = mimes and list(mimes) or []
        
        self.parsers = []
        self.validators = []

    
    def _register(self, lst, prio, val):
        self.parser.append((prio, val))
        self.parser.sort(key=lambda x: x[0], reverse=True)
    
    def _unregister(self, lst, obj):
        dlist = []
        for i in lst:
            if i[1] == obj:
                dlist.append(i)
        for i in dlist:
            lst.remove(i)
    
        
    def register_parser(self, parser, priority = PRIO_DEFAULT):
        self._register(self.parsers, priority, parser)
        
    def unregister_parser(self, parser):
        self._unregister(self.parsers, parser)
    
    def register_validator(self, validator, priority = PRIO_DEFAULT):
        """
        Register a Validator for this DocType.
        """
        self._register(self.validators, priority, validator)
        
    def unregister_validator(self, validator):
        """
        Unregister a validator
        """
        self._unregister(self.validators, validator)


    def get_best_parser(self):
        if self.parsers:
            return self.parsers[0]
        return None

    def __unicode__(self):
        return self.human

    def __repr__(self):
        return '<DocType %s %s>' %(self.internal, self.human)

class TypeManager(dict):
    
    def __init__(self):
        self._globs = {}
        self._mimetypes = {}
    
    def add(self, doctype):
        if self.has_key(doctype.internal):
            raise "doctype already registed"
        self[doctype.internal] = doctype
        for ext in doctype.extensions:
            if self._globs.has_key(ext):
                self._globs[ext].append(doctype)
            else:
                self._globs[ext] = [doctype]
        
    
    def _parse_map(self, lst):
        for intname, vars in lst.iteritems():
            nd = DocType(intname, vars[0], aliases=vars[1], extensions=vars[2], 
                         mimes=vars[3])
            self.add(nd)

    def types_by_filename(self, filename):
        """Returns a list of DocTypes matching for the given filename"""
        rv = []
        for test in self._globs.keys():
            if fnmatch.fnmatch(filename, test):
                rv += self._globs[test]
        
        return rv
        
    def type_by_filename(self, filename):
        """Tries to find only one, the best guess for the type."""
        best = None
        best_glob = ""
        for test in self._globs.keys():
            if fnmatch.fnmatch(filename, test):
                if len(test) > len(best_glob):
                    best_glob = test
                    best_list += self._globs[test]
        if len(best_list) > 1:
            # erks. got more then one result. try different approach
            # guess the mimetype through the python mimetype lib
            #import mimetypes
            gtest = None
            import subprocess
            try:
                gtest = subprocess.Popen(['file', '-bzki', filename], stdout=subprocess.PIPE).communicate()[0].strip()
                if gtest.find(';') != -1:
                    gtest = gtest[:gtest.find(';')]
            except OSError:
                pass
            if gtest:
                for dt in best_list:
                    if mtest in dt.mimes:
                        best = dt
            else:
                # use the first one as total fallback :(
                best = best_list[0]
        else:
            best = best_list[0]
        
        return best


Manager = TypeManager()
Manager._parse_map(_DEFMAPPING)

