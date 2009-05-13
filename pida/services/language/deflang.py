DEFMAPPING = {
 'ActionScript': {'alias': ('as', 'actionscript'),
                  'glob': ('*.as',),
                  'human': 'ActionScript',
                  'mime': ('application/x-actionscript',
                           'text/x-actionscript',
                           'text/actionscript'),
                  'section': 'Others'},
 'Ada': {'alias': (),
                  'glob': ('*.ada','*.adb','*.adc'),
                  'human': 'Ada',
                  'mime': (),
                  'section': 'Sources'},
 'ApacheConf': {'alias': ('apacheconf', 'aconf', 'apache'),
                'glob': ('.htaccess', 'apache.conf', 'apache2.conf'),
                'human': 'ApacheConf',
                'mime': ('text/x-apacheconf',),
                'section': 'Configs'},
 'ASP': {'alias': ('ActiveServerPages', 'Active Server Pages'),
                  'glob': ('*.asp'),
                  'human': 'ASP',
                  'mime': ('text/x-asp','application/x-asp','application/x-asap'),
                  'section': 'Scripts'},
 'awk': {'alias': ('AWK'),
                  'glob': ('*.awk'),
                  'human': 'AWK',
                  'mime': ('application/x-awk'),
                  'section': 'Scripts'},
 'BBCode': {'alias': ('bbcode',),
            'glob': (),
            'human': 'BBCode',
            'mime': ('text/x-bbcode',),
            'section': 'Others'},
 'Bash': {'alias': ('bash', 'sh'),
          'glob': ('*.sh',),
          'human': 'Bash',
          'mime': ('application/x-sh', 'application/x-shellscript',
                   'text/x-shellscript', 'text/x-sh'),
          'section': 'Scripts'},
 'Batch': {'alias': ('bat', 'dosbatch', 'Dos Batch'),
           'glob': ('*.bat', '*.cmd'),
           'human': 'Dos Batchfile',
           'mime': ('application/x-dos-batch',),
           'section': 'Scripts'},
 'Befunge': {'alias': ('befunge',),
             'glob': ('*.befunge',),
             'human': 'Befunge',
             'mime': ('application/x-befunge',),
             'section': 'Others'},
 'Boo': {'alias': ('boo',),
         'glob': ('*.boo',),
         'human': 'Boo',
         'mime': ('text/x-boo',),
         'section': 'Others'},
 'Brainfuck': {'alias': ('brainfuck', 'bf'),
               'glob': ('*.bf', '*.b'),
               'human': 'Brainfuck',
               'mime': ('application/x-brainfuck',),
               'section': 'Others'},
 'C': {'alias': ('c',),
       'glob': ('*.c', '*.h'),
       'human': 'C',
       'mime': ('text/x-chdr', 'text/x-csrc'),
       'section': 'Sources'},
 'Cpp': {'alias': ('C++','CPP'),
       'glob': ('*.cpp','*.cxx','*.cc','*.C','*.c++'),
       'human': 'C++',
       'mime': ('text/x-c++','text/x-cpp','text/x-c++src',),
       'section': 'Sources'},
 'ChangeLog': {'alias': ('Change Log','changelog'),
       'glob': ('ChangeLog', 'changelog'),
       'human': 'ChangeLog',
       'mime': (),
       'section': 'Others'},
 'CIL': {'alias': ('cil','msil'),
       'glob': (),
       'human': 'CIL',
       'mime': ('text/x-msil', 'text/x-cil'),
       'section': 'Sources'},
 'CMake': {'alias': ('cmake',),
              'glob': ('CMakeLists.txt','*.cmake','*.cmake.in','*.ctest','*.ctest.in'),
              'human': 'CMake',
              'mime': (),
              'section': 'Others'},
 'CObjdump': {'alias': ('c-objdump',),
              'glob': ('*.c-objdump',),
              'human': 'c-objdump',
              'mime': ('text/x-c-objdump',),
              'section': 'Sources'},
 'CSharp': {'alias': ('csharp', 'c#'),
            'glob': ('*.cs',),
            'human': 'C#',
            'mime': ("text/x-csharpsrc","text/x-csharp"),
            'section': 'Sources'},
 'CommonLisp': {'alias': ('common-lisp', 'cl'),
                'glob': ('*.cl', '*.lisp', '*.el'),
                'human': 'Common Lisp',
                'mime': ('text/x-common-lisp',),
                'section': 'Sources'},
 'Cpp': {'alias': ('cpp', 'c++'),
         'glob': ('*.cpp', '*.hpp', '*.c++', '*.h++'),
         'human': 'C++',
         'mime': ('text/x-c++hdr', 'text/x-c++src'),
         'section': 'Sources'},
 'CppObjdump': {'alias': ('cpp-objdump', 'c++-objdumb', 'cxx-objdump'),
                'glob': ('*.cpp-objdump', '*.c++-objdump', '*.cxx-objdump'),
                'human': 'cpp-objdump',
                'mime': ('text/x-cpp-objdump',),
                'section': 'Sources'},
 'Css': {'alias': ('css',),
         'glob': ('*.css',),
         'human': 'CSS',
         'mime': ('text/css',),
         'section': 'Web'},
 'CssDjango': {'alias': ('css+django', 'css+jinja'),
               'glob': (),
               'human': 'CSS+Django/Jinja',
               'mime': ('text/css+django', 'text/css+jinja'),
               'section': 'Web'},
 'CssErb': {'alias': ('css+erb', 'css+ruby'),
            'glob': (),
            'human': 'CSS+Ruby',
            'mime': ('text/css+ruby',),
            'section': 'Web'},
 'CssGenshi': {'alias': ('css+genshitext', 'css+genshi'),
               'glob': (),
               'human': 'CSS+Genshi Text',
               'mime': ('text/css+genshi',),
               'section': 'Web'},
 'CssPhp': {'alias': ('css+php',),
            'glob': (),
            'human': 'CSS+PHP',
            'mime': ('text/css+php',),
            'section': 'Web'},
 'CssSmarty': {'alias': ('css+smarty',),
               'glob': (),
               'human': 'CSS+Smarty',
               'mime': ('text/css+smarty',),
               'section': 'Web'},
 'D': {'alias': ('d',),
       'glob': ('*.d', '*.di'),
       'human': 'D',
       'mime': ('text/x-dsrc',),
       'section': 'Sources'},
 'Docbook': {'alias': ('docbook',),
              'glob': ('*.docbook',),
              'human': 'Docbook',
              'mime': ('application/docbook+xml',),
              'section': 'Others'},
 'Dot': {'alias': ('graphviz dot','graphviz'),
              'glob': ('*.dot','*.gv'),
              'human': 'Graphviz dot',
              'mime': ('text/vnd.graphviz',),
              'section': 'Others'},
 'DObjdump': {'alias': ('d-objdump',),
              'glob': ('*.d-objdump',),
              'human': 'd-objdump',
              'mime': ('text/x-d-objdump',),
              'section': 'Others'},
 'DebianControl': {'alias': ('control',),
                   'glob': ('control',),
                   'human': 'Debian Control file',
                   'mime': (),
                   'section': 'Configs'},
 'Delphi': {'alias': ('delphi', 'pas', 'pascal', 'objectpascal'),
            'glob': ('*.pas',),
            'human': 'Delphi',
            'mime': ('text/x-pascal',),
            'section': 'Sources'},
 'Diff': {'alias': ('diff',),
          'glob': ('*.diff', '*.patch'),
          'human': 'Diff',
          'mime': ('text/x-diff', 'text/x-patch'),
          'section': 'Others'},
 'Django': {'alias': ('django', 'jinja'),
            'glob': (),
            'human': 'Django/Jinja',
            'mime': ('application/x-django-templating',
                     'application/x-jinja'),
            'section': 'Web'},
 'DPatch': {'alias': (),
              'glob': ('*.dpatch',),
              'human': 'DPatch',
              'mime': ('text/x-dpatch',),
              'section': 'Others'},
 'DTD': {'alias': ('Document Type Definition',),
              'glob': ('*.dtd',),
              'human': 'DPatch',
              'mime': ('text/x-dtd',),
              'section': 'Others'},
 'Dylan': {'alias': ('dylan',),
           'glob': ('*.dylan',),
           'human': 'Dylan',
           'mime': ('text/x-dylan',),
           'section': 'Sources'},
 'Eiffel': {'alias': (),
         'glob': ('*.e','*.eif'),
         'human': 'Eiffel',
         'mime': ('text/x-eiffel',),
         'section': 'Sources'},

 'Erb': {'alias': ('erb',),
         'glob': (),
         'human': 'ERB',
         'mime': ('application/x-ruby-templating',),
         'section': 'Others'},
 'Erlang': {'alias': ('erlang',),
            'glob': ('*.erl', '*.hrl'),
            'human': 'Erlang',
            'mime': ('text/x-erlang',),
            'section': 'Sources'},
 'Forth': {'alias': ('forth',),
            'glob': ('*.frt', '*.fs'),
            'human': 'Forth',
            'mime': ('text/x-forth',),
            'section': 'Sources'},
 'Fortran': {'alias': ('Fortran 95',),
            'glob': ('*.f','*.f9[05]','*.for'),
            'human': 'Fortran 95',
            'mime': ('text/x-fortran',),
            'section': 'Sources'},
 'Gas': {'alias': ('gas',),
         'glob': ('*.s', '*.S'),
         'human': 'GAS',
         'mime': ('text/x-gas',),
         'section': 'Others'},
 'Genshi': {'alias': ('genshi', 'kid', 'xml+genshi', 'xml+kid'),
            'glob': ('*.kid',),
            'human': 'Genshi',
            'mime': ('application/x-genshi', 'application/x-kid'),
            'section': 'Markup'},
 'GenshiText': {'alias': ('genshitext',),
                'glob': (),
                'human': 'Genshi Text',
                'mime': ('application/x-genshi-text', 'text/x-genshi'),
                'section': 'Others'},
 'Gettext': {'alias': ('pot', 'po'),
             'glob': ('*.pot', '*.po'),
             'human': 'Gettext Catalog',
             'mime': ('application/x-gettext',
                      'text/x-gettext',
                      'text/gettext'),
             'section': 'Others'},
 'GtkDoc': {'alias': ('gtk-doc', 'gtkdoc'),
             'glob': (),
             'human': 'GTK Doc',
             'mime': (),
             'section': 'Markup'},
 'GtkRc': {'alias': ('GtkRC', 'GTK Resource Config'),
             'glob': ('gtkrc','.gtkrc','gtkrc-*','.gtkrc-*'),
             'human': 'GtkRC',
             'mime': (),
             'section': 'Configs'},

 'Groff': {'alias': ('groff', 'nroff', 'man'),
           'glob': ('*.[1234567]', '*.man'),
           'human': 'Groff',
           'mime': ('application/x-troff', 'text/troff'),
           'section': 'Others'},
 'Haddock': {'alias': (),
             'glob': (),
             'human': 'Haddock',
             'mime': (),
             'section': 'Markup'},
 'Haskell': {'alias': ('haskell', 'hs'),
             'glob': ('*.hs',),
             'human': 'Haskell',
             'mime': ('text/x-haskell',),
             'section': 'Sources'},
 'HaskellLiterate': {'alias': ('Haskell Literate', 'Literate Haskell'),
             'glob': ('*.lhs',),
             'human': 'Haskell Literate',
             'mime': ('text/x-literate-haskell',),
             'section': 'Sources'},

 'Html': {'alias': ('html',),
          'glob': ('*.html', '*.htm', '*.xhtml'),
          'human': 'HTML',
          'mime': ('text/html', 'application/xhtml+xml'),
          'section': 'Markup'},
 'HtmlDjango': {'alias': ('html+django', 'html+jinja'),
                'glob': (),
                'human': 'HTML+Django/Jinja',
                'mime': ('text/html+django', 'text/html+jinja'),
                'section': 'Markup'},
 'HtmlGenshi': {'alias': ('html+genshi', 'html+kid'),
                'glob': (),
                'human': 'HTML+Genshi',
                'mime': ('text/html+genshi',),
                'section': 'Markup'},
 'HtmlPhp': {'alias': ('html+php',),
             'glob': ('*.phtml',),
             'human': 'HTML+PHP',
             'mime': ('application/x-php',
                      'application/x-httpd-php',
                      'application/x-httpd-php3',
                      'application/x-httpd-php4',
                      'application/x-httpd-php5'),
             'section': 'Markup'},
 'HtmlSmarty': {'alias': ('html+smarty',),
                'glob': (),
                'human': 'HTML+Smarty',
                'mime': ('text/html+smarty',),
                'section': 'Markup'},
 'Idl': {'alias': ('IDL',),
         'glob': ('*.idl',),
         'human': 'IDL',
         'mime': ('text/x-idl',),
         'section': 'Sources'},
 'Ini': {'alias': ('ini', 'cfg'),
         'glob': ('*.ini', '*.cfg'),
         'human': 'INI',
         'mime': ('text/x-ini',),
         'section': 'Configs'},
 'IrcLogs': {'alias': ('irc',),
             'glob': ('*.weechatlog',),
             'human': 'IRC logs',
             'mime': ('text/x-irclog',),
             'section': 'Others'},
 'Java': {'alias': ('java',),
          'glob': ('*.java',),
          'human': 'Java',
          'mime': ('text/x-java',),
          'section': 'Sources'},
 'Javascript': {'alias': ('js', 'javascript'),
                'glob': ('*.js',),
                'human': 'JavaScript',
                'mime': ('application/x-javascript',
                         'application/javascript',
                         'text/x-javascript',
                         'text/javascript',
                         'text/x-js'),
                'section': 'Scripts'},
 'JavascriptDjango': {'alias': ('js+django',
                                'javascript+django',
                                'js+jinja',
                                'javascript+jinja'),
                      'glob': (),
                      'human': 'JavaScript+Django/Jinja',
                      'mime': ('application/x-javascript+django',
                               'application/x-javascript+jinja',
                               'text/x-javascript+django',
                               'text/x-javascript+jinja',
                               'text/javascript+django',
                               'text/javascript+jinja'),
                      'section': 'Scripts'},
 'JavascriptErb': {'alias': ('js+erb',
                             'javascript+erb',
                             'js+ruby',
                             'javascript+ruby'),
                   'glob': (),
                   'human': 'JavaScript+Ruby',
                   'mime': ('application/x-javascript+ruby',
                            'text/x-javascript+ruby',
                            'text/javascript+ruby'),
                   'section': 'Scripts'},
 'JavascriptGenshi': {'alias': ('js+genshitext',
                                'js+genshi',
                                'javascript+genshitext',
                                'javascript+genshi'),
                      'glob': (),
                      'human': 'JavaScript+Genshi Text',
                      'mime': ('application/x-javascript+genshi',
                               'text/x-javascript+genshi',
                               'text/javascript+genshi'),
                      'section': 'Scripts'},
 'JavascriptPhp': {'alias': ('js+php', 'javascript+php'),
                   'glob': (),
                   'human': 'JavaScript+PHP',
                   'mime': ('application/x-javascript+php',
                            'text/x-javascript+php',
                            'text/javascript+php'),
                   'section': 'Scripts'},
 'JavascriptSmarty': {'alias': ('js+smarty', 'javascript+smarty'),
                      'glob': (),
                      'human': 'JavaScript+Smarty',
                      'mime': ('application/x-javascript+smarty',
                               'text/x-javascript+smarty',
                               'text/javascript+smarty'),
                      'section': 'Scripts'},
 'Jsp': {'alias': ('jsp',),
         'glob': ('*.jsp',),
         'human': 'Java Server Page',
         'mime': ('application/x-jsp',),
         'section': 'Web'},
 'Latex': {'alias': ('LaTeX', 'TEX'),
                     'glob': ('*.tex','*.ltx','*.sty','*.cls','*.dtx','*.ins','*.bbl'),
                     'human': 'LaTeX',
                     'mime': ('text/x-tex',),
                     'section': 'Markup'},
 'LiterateHaskell': {'alias': ('lhs', 'literate-haskell'),
                     'glob': ('*.lhs',),
                     'human': 'Literate Haskell',
                     'mime': ('text/x-literate-haskell',),
                     'section': 'Sources'},
 'Libtool': {'alias': (),
                     'glob': ('*.la','*.lai','*.lo'),
                     'human': 'libtool',
                     'mime': ('text/x-libtool',),
                     'section': 'Others'},
 'Llvm': {'alias': ('llvm',),
          'glob': ('*.ll',),
          'human': 'LLVM',
          'mime': ('text/x-llvm',),
          'section': 'Others'},
 'Lua': {'alias': ('lua',),
         'glob': ('*.lua',),
         'human': 'Lua',
         'mime': ('text/x-lua', 'application/x-lua'),
         'section': 'Scripts'},
 'M4': {'alias': ('m4', ),
                     'glob': ('*.m4','configure.ac','configure.in'),
                     'human': 'm4',
                     'mime': ('application/x-m4',),
                     'section': 'Scripts'},

 'MOOCode': {'alias': ('moocode',),
             'glob': ('*.moo',),
             'human': 'MOOCode',
             'mime': ('text/x-moocode',),
             'section': 'Others'},
 'Makefile': {'alias': ('make', 'makefile', 'mf'),
              'glob': ('*.mak', 'Makefile', 'makefile', 
                       'GNUmakefile','[Mm]akefile.*'),
              'human': 'Makefile',
              'mime': ('text/x-makefile',),
              'section': 'Others'},
 'Mako': {'alias': ('mako',),
          'glob': ('*.mao',),
          'human': 'Mako',
          'mime': ('application/x-mako',),
          'section': 'Others'},
 'MakoCss': {'alias': ('css+mako',),
             'glob': (),
             'human': 'CSS+Mako',
             'mime': ('text/css+mako',),
             'section': 'Others'},
 'MakoHtml': {'alias': ('html+mako',),
              'glob': (),
              'human': 'HTML+Mako',
              'mime': ('text/html+mako',),
              'section': 'Markup'},
 'MakoJavascript': {'alias': ('js+mako', 'javascript+mako'),
                    'glob': (),
                    'human': 'JavaScript+Mako',
                    'mime': ('application/x-javascript+mako',
                             'text/x-javascript+mako',
                             'text/javascript+mako'),
                    'section': 'Markup'},
 'MakoXml': {'alias': ('xml+mako',),
             'glob': (),
             'human': 'XML+Mako',
             'mime': ('application/xml+mako',),
             'section': 'Others'},
 'MiniD': {'alias': ('minid',),
           'glob': ('*.md',),
           'human': 'MiniD',
           'mime': ('text/x-minidsrc',),
           'section': 'Others'},
 'MoinWiki': {'alias': ('trac-wiki', 'moin'),
              'glob': (),
              'human': 'MoinMoin/Trac Wiki markup',
              'mime': ('text/x-trac-wiki',),
              'section': 'Others'},
 'MuPAD': {'alias': 'MuPAD',
           'glob': ('mupad',),
           'human': 'pygments.s.math',
           'mime': ('*.mu',),
           'section': 'Others'},
 'Myghty': {'alias': ('myghty',),
            'glob': ('*.myt', 'autodelegate'),
            'human': 'Myghty',
            'mime': ('application/x-myghty',),
            'section': 'Others'},
 'MyghtyCss': {'alias': ('css+myghty',),
               'glob': (),
               'human': 'CSS+Myghty',
               'mime': ('text/css+myghty',),
               'section': 'Others'},
 'MyghtyHtml': {'alias': ('html+myghty',),
                'glob': (),
                'human': 'HTML+Myghty',
                'mime': ('text/html+myghty',),
                'section': 'Others'},
 'MyghtyJavascript': {'alias': ('js+myghty', 'javascript+myghty'),
                      'glob': (),
                      'human': 'JavaScript+Myghty',
                      'mime': ('application/x-javascript+myghty',
                               'text/x-javascript+myghty',
                               'text/javascript+mygthy'),
                      'section': 'Others'},
 'MyghtyXml': {'alias': ('xml+myghty',),
               'glob': (),
               'human': 'XML+Myghty',
               'mime': ('application/xml+myghty',),
               'section': 'Others'},
 'Nemerle': {'alias': (),
               'glob': ('*.n',),
               'human': 'Nemerle',
               'mime': ('text/x-nemerle',),
               'section': 'Sources'},
 'NSIS': {'alias': (),
               'glob': ('*.nsi','*.nsh',),
               'human': 'NSIS',
               'mime': ('text/x-nsis',),
               'section': 'Others'},

 'Objdump': {'alias': ('objdump',),
             'glob': ('*.objdump',),
             'human': 'objdump',
             'mime': ('text/x-objdump',),
             'section': 'Others'},
 'ObjectiveC': {'alias': ('objective-c', 'objectivec', 'obj-c', 'objc'),
                'glob': ('*.m',),
                'human': 'Objective-C',
                'mime': ('text/x-objective-c', 'text/x-objcsrc'),
                'section': 'Sources'},
 'Ocaml': {'alias': ('ocaml', 'Objective Caml', 'objective-caml'),
           'glob': ('*.ml', '*.mli', '*.mll', '*.mly'),
           'human': 'OCaml',
           'mime': ('text/x-ocaml',),
           'section': 'Sources'},
 'Ocl': {'alias': ('OCL',),
           'glob': ('*.ocl'),
           'human': 'OCL',
           'mime': ('text/x-ocl',),
           'section': 'Sources'},
 'Pascal': {'alias': ('pascal'),
          'glob': ('*.p', '*.pas'),
          'human': 'Pascal',
          'mime': ('text/x-pascal'),
          'section': 'Sources'},
 'Perl': {'alias': ('perl', 'pl'),
          'glob': ('*.pl', '*.pm', '*.al', '*.perl'),
          'human': 'Perl',
          'mime': ('text/x-perl', 'application/x-perl'),
          'section': 'Scripts'},
 'Php': {'alias': ('php', 'php3', 'php4', 'php5'),
         'glob': ('*.php', '*.php[345]', '*.phtml'),
         'human': 'PHP',
         'mime': ('text/x-php', 'application/x-php', 'text/x-php-source',
                  'application/x-php-source'),
         'section': 'Scripts'},
 'Pkgconfig': {'alias': ('pkg-config', 'pkgconfig', 'pkg config'),
            'glob': ('*.pc'),
            'human': 'pkg-config',
            'mime': ('text/x-pkg-config'),
            'section': 'Configs'},
 'Po': {'alias': ('gettext translation', 'po', 'gettext-translation'),
            'glob': ('*.po', '*.pot'),
            'human': 'Gettext Translation',
            'mime': ('text/x-po','text/x-pot','text/x-pox',
                     'text/x-gettext-translation',
                     'text/x-gettext-translation-template'),
            'section': 'Others'},
 'Prolog': {'alias': (),
            'glob': ('*.prolog'),
            'human': 'Prolog',
            'mime': ('text/x-prolog'),
            'section': 'Others'},
 'Python': {'alias': ('python', 'py'),
            'glob': ('*.py', '*.pyw', '*.sc', 'SConstruct', 'SConscript'),
            'human': 'Python',
            'mime': ('text/x-python', 'application/x-python'),
            'section': 'Scripts'},
 'PythonConsole': {'alias': ('pycon', 'python-console'),
                   'glob': (),
                   'human': 'Python console session',
                   'mime': ('text/x-python-doctest',),
                   'section': 'Others'},
 'PythonTraceback': {'alias': ('pytb',),
                     'glob': ('*.pytb',),
                     'human': 'Python Traceback',
                     'mime': ('text/x-python-traceback',),
                     'section': 'Others'},
# 'R': {'alias': ('r',),
#              'glob': ('*.R','*.Rout','*.r','*.Rhistory','*.Rt',
#              '*.Rout.save','*.Rout.fail'),
#              'human': 'R',
#              'mime': ('text/x-R',),
#              'section': 'Others'},
 'RawToken': {'alias': ('raw',),
              'glob': ('*.raw',),
              'human': 'Raw token data',
              'mime': ('application/x-pygments-tokens',),
              'section': 'Others'},
 'Redcode': {'alias': ('redcode',),
             'glob': ('*.cw',),
             'human': 'Redcode',
             'mime': (),
             'section': 'Others'},
 'Rhtml': {'alias': ('rhtml', 'html+erb', 'html+ruby'),
           'glob': ('*.rhtml',),
           'human': 'RHTML',
           'mime': ('text/html+ruby',),
           'section': 'Markup'},
 'Rpmspec': {'alias': ('RPM Spec', 'RPM-Spec',),
         'glob': ('*.spec'),
         'human': 'RPM spec',
         'mime': ('text/x-rpm-spec',),
         'section': 'Others'},
 'Rst': {'alias': ('rst', 'rest', 'restructuredtext'),
         'glob': ('*.rst', '*.rest'),
         'human': 'reStructuredText',
         'mime': ('text/x-rst',),
         'section': 'Others'},
 'Ruby': {'alias': ('rb', 'ruby'),
          'glob': ('*.rb',
                   '*.rbw',
                   'Rakefile',
                   '*.rake',
                   '*.gemspec',
                   '*.rbx'),
          'human': 'Ruby',
          'mime': ('text/x-ruby', 'application/x-ruby'),
          'section': 'Scripts'},
 'RubyConsole': {'alias': ('rbcon', 'irb'),
                 'glob': (),
                 'human': 'Ruby irb session',
                 'mime': ('text/x-ruby-shellsession',),
                 'section': 'Others'},
 'Scheme': {'alias': ('scheme', 'scm'),
            'glob': ('*.scm',),
            'human': 'Scheme',
            'mime': ('text/x-scheme', 'application/x-scheme'),
            'section': 'Others'},
 'Smarty': {'alias': ('smarty',),
            'glob': ('*.tpl',),
            'human': 'Smarty',
            'mime': ('application/x-smarty',),
            'section': 'Others'},
 'SourcesList': {'alias': ('sourceslist', 'sources.list'),
                 'glob': ('sources.list',),
                 'human': 'Debian Sourcelist',
                 'mime': (),
                 'section': 'Configs'},
 'Sql': {'alias': ('sql',),
         'glob': ('*.sql',),
         'human': 'SQL',
         'mime': ('text/x-sql',),
         'section': 'Others'},
 'SquidConf': {'alias': ('squidconf', 'squid.conf', 'squid'),
               'glob': ('squid.conf',),
               'human': 'SquidConf',
               'mime': ('text/x-squidconf',),
               'section': 'Others'},
 'Tcl': {'alias': (),
          'glob': ('*.tcl','*.tk'),
          'human': 'Tcl',
          'mime': ('text/x-tcl', 'application/x-tcl'),
          'section': 'Scripts'},
 'Text': {'alias': ('text',),
          'glob': ('*.txt',),
          'human': 'Text only',
          'mime': ('text/plain',),
          'section': 'Others'},
 'Texinfo': {'alias': ('texinfo', 'tex info', 'tex-info'),
          'glob': ('*.texi', '*.texinfo'),
          'human': 'Text only',
          'mime': ('text/x-texinfo',),
          'section': 'Markup'},
 'Vala': {'alias': (),
           'glob': ('*.vala'),
           'human': 'Vala',
           'mime': ('text/x-vala',),
           'section': 'Sources'},
 'VbNet': {'alias': ('vb.net', 'vbnet'),
           'glob': ('*.vb', '*.bas'),
           'human': 'VB.net',
           'mime': ('text/x-vbnet', 'text/x-vba', 'text/x-vb'),
           'section': 'Others'},
 'Verilog': {'alias': (),
           'glob': ('*.v'),
           'human': 'Verilog',
           'mime': ('text/x-verilog-src',),
           'section': 'Sources'},
 'Vhdl': {'alias': ('VHDL',),
           'glob': ('*.vhd'),
           'human': 'VHDL',
           'mime': ('text/x-vhdl',),
           'section': 'Sources'},
 'Vim': {'alias': ('vim',),
         'glob': ('*.vim', '.vimrc'),
         'human': 'Vim',
         'mime': ('text/x-vim',),
         'section': 'Scripts'},
 'Xml': {'alias': ('xml',),
         'glob': ('*.xml', '*.xsl', '*.rss'),
         'human': 'XML',
         'mime': ('text/xml',
                  'application/xml',
                  'image/svg+xml',
                  'application/rss+xml',
                  'application/atom+xml',
                  'application/xsl+xml',
                  'application/xslt+xml'),
         'section': 'Markup'},
 'XmlDjango': {'alias': ('xml+django', 'xml+jinja'),
               'glob': (),
               'human': 'XML+Django/Jinja',
               'mime': ('application/xml+django', 'application/xml+jinja'),
               'section': 'Markup'},
 'XmlErb': {'alias': ('xml+erb', 'xml+ruby'),
            'glob': (),
            'human': 'XML+Ruby',
            'mime': ('application/xml+ruby',),
            'section': 'Markup'},
 'XmlPhp': {'alias': ('xml+php',),
            'glob': (),
            'human': 'XML+PHP',
            'mime': ('application/xml+php',),
            'section': 'Markup'},
 'XmlSmarty': {'alias': ('xml+smarty',),
               'glob': (),
               'human': 'XML+Smarty',
               'mime': ('application/xml+smarty',),
               'section': 'Markup'},
 'Xslt': {'alias': ('XSLT','xslt'),
               'glob': ('*.xsl', '*.xslt'),
               'human': 'XSLT',
               'mime': ('application/xslt+xml',),
               'section': 'Markup'},
 'Yacc': {'alias': ('bison',),
               'glob': ('*.yacc','*.y'),
               'human': 'Yacc',
               'mime': ('text/x-yacc','text/x-bison'),
               'section': 'Others'}
}
