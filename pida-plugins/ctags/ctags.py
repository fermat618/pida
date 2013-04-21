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
import tempfile
import subprocess
# gtk
import gtk

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig
from pida.core.languages import (LanguageService, Outliner, Validator,
    Completer, LanguageServiceFeaturesConfig, LanguageInfo, Definer, Documentator)

from pida.utils.languages import LANG_PRIO, OutlineItem

# locale
from pida.core.locale import Locale
locale = Locale('python')
_ = locale.gettext
from subprocess import Popen, PIPE


def build_language_list(typemanager):
    """
    Build a list of language internal names from the output of 
    ctags --list-languages
    """
    try:
        output = Popen(["ctags", "--list-languages"], 
                       stdout=PIPE).communicate()[0]
    except OSError as e:
        # can't find ctags -> no support :-)
        return []
    output = output.splitlines()
    rv = []
    if "C#" in output:
        output.append("vala")
    for name in output:
        clang = typemanager.get_fuzzy(name)
        if clang is not None:
            rv.append(clang)

    return rv

from pida.services.language import DOCTYPES

SUPPORTED_LANGS = build_language_list(DOCTYPES)
# class PythonActionsConfig(ActionsConfig):
#
#     def create_actions(self):
#         self.create_action(
#             'execute_python',
#             TYPE_NORMAL,
#             _('Execute Python Module'),
#             _('Execute the current Python module in a shell'),
#             gtk.STOCK_EXECUTE,
#             self.on_python_execute,
#         )
#
#     def on_python_execute(self, action):
#         self.svc.execute_current_document()
#

class CtagsTokenList(object):
    def __init__(self, *args, **kwargs):
        self._count = 0
        self._items = {}
        self._names = {}
        self._all_parent_id_updated = False

    def add(self, item):
        if item.filename is None:
            return
        if item.filename not in self._items:
            self._items[item.filename] = []
            self._names[item.filename] = {}
        self._items[item.filename].append(item)
        cnames = self._names[item.filename]
        cnames[item.fullname] = item

        self._count += 1
        item.id = self._count
        item.parent_id = None
        self._all_parent_id_updated = False

    def update_parent_id(self):
        if self._all_parent_id_updated:
            return
        for j in self._items.values():
            for i in j:
                if i.parent is None and i.parent_name is not None:
                    i.parent = self.get_parent(i)
                    if i.parent is not None:
                        i.parent_id = i.parent.id
                        i.parent.is_parent = True
        self._all_parent_id_updated = True


    def filter_items(self, filename):
        self.update_parent_id()
        if filename not in self._items:
            return
        for i in self._items[filename]:
            yield i

    def clear(self):
        self._items.clear()
        self._names.clear()

    def clear_filename(self, filename):
        del self._items[filename]
        del self._names[filename]

    def get_parent(self, item):
        if item.parent is not None:
            return item.parent
        return self._names[item.filename].get(item.parent_name, None)

    def __iter__(self):
        self.update_parent_id()
        for j in self._items.values():
            for i in j:
                yield i

class CtagItem(OutlineItem):
    def __init__(self, *args, **kwargs):
        self.filename = None
        self.is_parent = False
        super(OutlineItem, self).__init__(*args, **kwargs)

    def _get_fullname(self):
        if self.parent_name is None:
            return self.name
        return "%s.%s" %(self.parent_name, self.name)

    fullname = property(_get_fullname)

    @property
    def type_markup(self):
        return self.type

    def get_markup(self):
        if self.is_parent:
            return '<b>{}</b>'.format(self.name)
        elif self.parent_id is not None:
            return '<i>{}</i>'.format(self.name)
        else:
            return '{}'.format(self.name)
    markup = property(get_markup)

    def __repr__(self):
        return "<CtagItem %s %s %s >" %(self.name, self.parent_name, self.fullname)

class CtagsOutliner(Outliner):

    priority = LANG_PRIO.GOOD
    name = "ctags"
    plugin = "ctags"
    description = _("A very fast but only shallow outliner")

    def run(self):
        if not self.document.filename:
            return
        try:
            filename, istmp = self._update_tagfile()
        except OSError as e:
            return
        tags = self._parse_tagfile(filename)

        if self.document.project:
            self.document.project['ctags_cache'] = tags
        if istmp:
            os.unlink(filename)
        items = list(tags.filter_items(self.document.filename))

        def pop_parent_first(item):
            p = item.parent
            if p is not None and p in items:
                for i in pop_parent_first(p):
                    yield i
            else:
                items.remove(item)
                yield item
        while len(items) != 0:
            item = items[0]
            for x in pop_parent_first(item):
                yield x


    def _update_tagfile(self, options = ("-n",), temp=False):
        """ filestr is a string, could be *.* or explicit paths """

        # create tempfile
        if self.document.project is None or temp:
            h, taglib = tempfile.mkstemp()
            os.close(h)
            temp = True
        else:
            taglib = os.path.join(self.document.project.get_meta_dir('ctags'),
                                  'lib.ctags')
        # launch ctags
        if self.document.doctype and self.document.doctype.internal == 'Vala':
            options = options + ('--language-force=C#',)
        command = ("ctags",) + options + ("-f", taglib, self.document.filename)
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError as e:
            self.log.error('failed execute ctags. Returned {rv}',
                    rv=e.returncode)
            raise OSError("can't execute ctags")
        
        return (taglib, temp)

    def _parse_tagfile(self, tagfile):
        """ Parse the given document and write the tags to a gtk.TreeModel.
        
        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel. """
        #TODO: the type is language dependent, and tagfile should by parsed 
        # language dependent.

        # refactoring noise    
        #doc = self.document
        #ls = self.model        
        #ls.clear()
        #tmpfile = self._generate_tagfile_from_document(doc)
        #if tmpfile is None: return ls
        
        # A list of lists. Matches the order found in tag files.
        # identifier, path to file, line number, type, and then more magical things
        tokenlist = [] 
        rv = CtagsTokenList()
        #names = {}
        h = open(tagfile)
        for r in h.readlines():
            tokens = r.strip().split("\t")
            if tokens[0][:2] == "!_": continue

            # convert line numbers to an int
            tokens[2] =  int(''.join(x for x in tokens[2] if x in '1234567890'))
            
            tokenlist.append(tokens)
        h.close()

        for tokens in tokenlist:
        
            parent_name = self._get_parent(tokens)
            
            # escape blanks in file path
            # FIXME
            #tokens[1] =  str( gnomevfs.get_uri_from_local_path(tokens[1]) )
            
            # make sure tokens[4] contains type code
            if len(tokens) == 3:
                tokens.append("")
            else:
                tokens[3] = self._get_type(tokens)
            
            item = CtagItem(name=tokens[0],
                            filename=tokens[1],
                            linenumber=int(tokens[2]),
                            type=tokens[3],
                            filter_type=tokens[3],
                            parent_name=parent_name)
            rv.add(item)
        return rv

    def _get_type(self, tokrow):
        """ Returns a char representing the token type or False if none were found.

        According to the ctags docs, possible types are:
        c   class name
        d   define (from #define XXX)
        e   enumerator
        f   function or method name
        F   file name
        g   enumeration name
        m   member (of structure or class data)
        p   function prototype
        s   structure name
        t   typedef
        u   union name
        v   variable        
        """
        def v2t(i):
            mapping = {
                'm': 'member',
                'c': 'class',
                'd': 'define',
                'e': 'enumeration',
                'f': 'function',
                'g': 'enumeration_name',
                'n': 'namespace',
                'p': 'prototype',
                's': 'structure',
                't': 'typedef',
                'u': 'union',
                'v': 'variable',
            }
            return mapping.get(i, 'unknown')

        if len(tokrow) == 4 and isinstance(tokrow[3], int):
            return tokrow[3]
        if len(tokrow) == 3: return
        for i in tokrow[3:]:
            if len(i) == 1:
                return v2t(i)  # most common case: just one char
            elif i[:4] == "kind":
                return v2t(i[5:])
            return 'unknown'
        return 'unknown'


    def _get_container_name(self, tokrow):
        """ Usually, we can assume that the parent's name is the same
            as the name of the token. In some cases (typedefs), this
            doesn't work (see Issue 13) """
        
        if self._get_type(tokrow) == "t":
            try:
                t = tokrow[4]
                a = t.split(":")
                return a[len(a)-1]
            except:
                pass
        return tokrow[0]
    
        
    # def _is_container(self, tokrow):
    #     """ class, enumerations, structs and unions are considerer containers.
    #         See Issue 13 for some issues we had with this.
    #     """
    #     # XXX: whether it is a container should be decided by whether it has 
    #     # children, not by type.
    #     return self._get_type(tokrow) in (
    #         'class', 'enumeration_name',
    #         'structure', 'union', 'typedef')

    def _get_parent(self, tokrow):
        if len(tokrow) <= 3: return
        # Iterate through all items in the tag.
        # TODO: Not sure if needed
        for i in tokrow[4:]:
            a = i.split(":", 1)
            # if a[0] in ("class","struct","union","enum"): 
            #     return a[1]
            if len(a) == 2:
                return a[1]
        return None


class Ctags(LanguageService):

    language_name = [x.internal for x in SUPPORTED_LANGS]
    outliner_factory = CtagsOutliner




# Required Service attribute for service loading
Service = Ctags



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
