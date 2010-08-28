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

from pida.utils.languages import (LANG_PRIO, LANG_OUTLINER_TYPES, OutlineItem )

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
    except OSError, e:
        # can't find ctags -> no support :-)
        return []
    output = output.splitlines()
    rv = []
    if "C#" in output:
        output.append("vala")
    for name in output:
        clang = typemanager.get_fuzzy(name)
        if clang:
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
        self._items = {}
        self._names = {}

    def add(self, item):
        if not self._items.has_key(item.filename):
            self._items[item.filename] = []
            self._names[item.filename] = {}
        self._items[item.filename].append(item)
        cnames = self._names[item.filename]
        cnames[item.fullname] = item

    def filter_items(self, filename):
        if not self._items.has_key(filename):
            return
        for i in self._items[filename]:
            if not i.parent and  i.parent_name:
                i.parent = self.get_parent(i)
            yield i

    def clear(self):
        self._items.clear()
        self._names.clear()

    def clear_filename(self, filename):
        del self._items[filename]
        del self._names[filename]

    def get_parent(self, item):
        if item.parent:
            return item.parent
        return self._names[item.filename].get(item.parent_name, None)

    def __iter__(self):
        for j in self._items.itervalues():
            for i in j:
                if not i.parent and  i.parent_name:
                    i.parent = self._names[i.filename].get(i.parent_name, None)
                yield i

class CtagItem(OutlineItem):
    def _get_fullname(self):
        if not self.parent_name:
            return self.name
        return "%s.%s" %(self.parent_name, self.name)
    fullname = property(_get_fullname)

    def __repr__(self):
        return "<CtagItem %s %s %s >" %(self.name, self.parent_name, self.fullname)

class CtagsOutliner(Outliner):

    priority = LANG_PRIO.GOOD
    name = "ctags"
    plugin = "ctags"
    description = _("A very fast but only shallow outliner")

    def get_outline(self):
        if not self.document.filename:
            return
        try:
            filename, istmp = self._update_tagfile()
        except OSError, e:
            return
        tags = self._parse_tagfile(filename)

        if self.document.project:
            self.document.project['ctags_cache'] = tags
        if istmp:
            os.unlink(filename)
        for node in tags.filter_items(self.document.filename):
            yield node


    def _update_tagfile(self, options = ("-n",), temp=False):
        """ filestr is a string, could be *.* or explicit paths """

        # create tempfile
        if not self.document.project or temp:
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
        #os.system(command)
        rv = subprocess.check_call(command)
        if rv:
            self.log.error('failed execute ctags. Returned %s' %rv)
            raise OSError, "can't execute ctags"
        
        return (taglib, temp)

    def _parse_tagfile(self, tagfile):
        """ Parse the given document and write the tags to a gtk.TreeModel.
        
        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel. """
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
            tokens[2] =  int(filter( lambda x: x in '1234567890', tokens[2] ))
            
            # prepend container elements, append member elements. Do this to
            # make sure that container elements are created first.
            if self._is_container(tokens): tokenlist = [tokens] + tokenlist
            else: tokenlist.append(tokens)
        h.close()

        # add tokens to the treestore---------------------------------------
        containers = { None: None } # keep dict: token's name -> treeiter
        
        # iterate through the list of tags, 
        # Note: Originally sorted by line number, bit it did break some
        # formatting in c
        #set_parents = []
        for tokens in tokenlist:
            #if not names.has_key(tokens[1]):
            #    names[tokens[1]] = {}
            #cnames = names[tokens[1]]
            # skip enums
            #if self.__get_type(tokens) in 'de': continue
        
            # append current token to parent iter, or to trunk when there is none
            parent_name = self._get_parent(tokens)
            is_container = self._is_container(tokens)
            #if parent in containers: node = containers[parent]
            #else:
            #    # create a dummy element in case the parent doesn't exist
            #    rv.append( None, [parent,"",0,""] )
            #    containers[parent] = node
            
            # escape blanks in file path
            # FIXME
            #tokens[1] =  str( gnomevfs.get_uri_from_local_path(tokens[1]) )
            
            # make sure tokens[4] contains type code
            if len(tokens) == 3: tokens.append("")
            else: tokens[3] = self._get_type(tokens)
            
            # append to treestore
            #it = ls.append( node, tokens[:4] )
            
            # if this element was a container, remember its treeiter
            #if self._is_container(tokens):
            #    containername = self._get_container_name(tokens)
            #    containers[ containername ] = it
            item = CtagItem(name=tokens[0],
                            filename=tokens[1],
                            linenumber=int(tokens[2]),
                            type=tokens[3],
                            filter_type=tokens[3],
                            is_container = is_container,
                            parent_name = parent_name)
            rv.add(item)
        return rv

    def _get_type(self, tokrow):
        """ Returns a char representing the token type or False if none were found.

        According to the ctags docs, possible types are:
		c	class name
		d	define (from #define XXX)
		e	enumerator
		f	function or method name
		F	file name
		g	enumeration name
		m	member (of structure or class data)
		p	function prototype
		s	structure name
		t	typedef
		u	union name
		v	variable        
        """
        def v2t(i):
            if i == 'm': return LANG_OUTLINER_TYPES.MEMBER
            if i == 'c': return LANG_OUTLINER_TYPES.CLASS
            if i == 'd': return LANG_OUTLINER_TYPES.DEFINE
            if i == 'e': return LANG_OUTLINER_TYPES.ENUMERATION
            if i == 'f': return LANG_OUTLINER_TYPES.FUNCTION
            if i == 'g': return LANG_OUTLINER_TYPES.ENUMERATION_NAME
            if i == 'n': return LANG_OUTLINER_TYPES.NAMESPACE
            if i == 'p': return LANG_OUTLINER_TYPES.PROTOTYPE
            if i == 's': return LANG_OUTLINER_TYPES.STRUCTURE
            if i == 't': return LANG_OUTLINER_TYPES.TYPEDEF
            if i == 'u': return LANG_OUTLINER_TYPES.UNION
            if i == 'v': return LANG_OUTLINER_TYPES.VARIABLE
            return LANG_OUTLINER_TYPES.UNKNOWN

        if len(tokrow) == 4 and isinstance(tokrow[3], int):
            return tokrow[3]
        if len(tokrow) == 3: return
        for i in tokrow[3:]:
            if len(i) == 1: 
                return v2t(i)# most common case: just one char
            elif i[:4] == "kind":
                return v2t(i[5:])
            return LANG_OUTLINER_TYPES.UNKNOWN
        return LANG_OUTLINER_TYPES.UNKNOWN


    def _get_container_name(self, tokrow):
        """ Usually, we can assume that the parent's name is the same
            as the name of the token. In some cases (typedefs), this
            doesn't work (see Issue 13) """
        
        if self.__get_type(tokrow) == "t":
            try:
                t = tokrow[4]
                a = t.split(":")
                return a[ len(a)-1 ]
            except:
                pass
        return tokrow[0]
    
        
    def _is_container(self, tokrow):
        """ class, enumerations, structs and unions are considerer containers.
            See Issue 13 for some issues we had with this.
        """
        if self._get_type(tokrow) in (
            LANG_OUTLINER_TYPES.CLASS,
            LANG_OUTLINER_TYPES.ENUMERATION_NAME,
            LANG_OUTLINER_TYPES.STRUCTURE,
            LANG_OUTLINER_TYPES.UNION,
            LANG_OUTLINER_TYPES.TYPEDEF): 
                return True
        return False
            
        # remove temp file
        #os.remove(tmpfile)

    def _get_parent(self, tokrow):
        if len(tokrow) == 3: return
        # Iterate through all items in the tag.
        # TODO: Not sure if needed
        for i in tokrow[3:]: 
            a = i.split(":")
            if a[0] in ("class","struct","union","enum"): 
                return a[1]
        return None


class Ctags(LanguageService):

    language_name = [x.internal for x in SUPPORTED_LANGS]
    outliner_factory = CtagsOutliner




# Required Service attribute for service loading
Service = Ctags



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
