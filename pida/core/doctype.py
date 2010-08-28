# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.doctype
    ~~~~~~~~~~~~~~~~~~

    :license: GPL2 or later
    :copyright: 2008 by The PIDA Project

"""

from glob import fnmatch
import charfinder
from collections import defaultdict

class DocType(object):
    """Represents a type of document. Like a python sourcecode file, a xml
    file, etc.
    """
    __slots__ = ('internal', 'aliases', 'human', 'extensions', 'mimes',
                 'section', 'parsers', 'validators', 'support')

    def __init__(self, internal, human, aliases=None, extensions=None,
                 mimes=None, section='Others'):
        self.internal = internal
        self.human = human
        self.aliases = aliases
        self.extensions = extensions
        self.mimes = mimes
        self.section = section
        # the support counter tracs how much support this document type gets
        # 0 means that he is currently not supported by something special
        self.support = 0

        self.parsers = []
        self.validators = []

    def inc_support(self):
        self.support += 1

    def dec_support(self):
        self.support -= 1
        # this can only happen if something decs more then supports it
        assert self.support >= 0

    @property
    def tooltip(self):
        rv = " ".join(self.aliases)
        if self.extensions:
            rv += " (%s)" % " ".join(self.extensions)
        return rv

    def __unicode__(self):
        return self.human

    def __repr__(self):
        return '<DocType %s %s>' % (self.internal, self.human)

class TypeManager(dict):
    """
    DocType Library

    This class manages a list of DocType instances and features selection
    """

    def __init__(self):
        self._globs = defaultdict(list)
        self._mimetypes = defaultdict(list)

    def add(self, doctype):
        if doctype.internal in self:
            raise "doctype already registed"
        self[doctype.internal] = doctype
        for ext in doctype.extensions:
            if ext:
                self._globs[ext].append(doctype)
        # we fill the list of known mimetypes as we see them
        for mime in doctype.mimes:
            charfinder.text_mime.add(mime)

    def _parse_map(self, lst):
        for intname, data in lst.iteritems():
            nd = DocType(intname, data['human'], aliases=data['alias'],
                         extensions=data['glob'], mimes=data['mime'],
                         section=data.get('section', None))

            self.add(nd)

    def guess_doctype_for_document(self, document):
        if not document.is_new:
            return self.type_by_filename(document.filename)
        # FIXME: need a setting for default language Type
        # or detect filetype somehow
        return None

    def types_by_filename(self, filename):
        """Returns a list of DocTypes matching for the given filename"""
        if not filename:
            #FIXME: return default type
            return []
        rv = []
        for test in self._globs.keys():
            if fnmatch.fnmatch(filename, test):
                rv += self._globs[test]

        return rv

    def type_by_filename(self, filename):
        """Tries to find only one, the best guess for the type."""
        if not filename:
            return None
        best = None
        best_glob = ""
        best_list = []
        for test in self._globs.keys():
            if fnmatch.fnmatch(filename, test):
                if len(test) > len(best_glob):
                    best_glob = test
                    best_list += self._globs[test]

        if best_glob == '':
            return None
        return self._globs[best_glob][0]

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
                    if gtest in dt.mimes:
                        best = dt
            else:
                # use the first one as total fallback :(
                best = best_list[0]
        elif len(best_list):
            best = best_list[0]

        return best

    def get_fuzzy(self, pattern):
        """
        Returns a fuzzy match to the pattern provided.
        A match is if any alias, the internal or human name
        match in lower case

        @pattern: string
        """
        pattern = pattern.lower()
        for lang in self.itervalues():
            if pattern == lang.internal.lower() or \
               pattern == lang.human.lower() or \
               any((pattern == x.lower() for x in lang.aliases)):
                return lang

    def get_fuzzy_list(self, pattern, substr=False):
        """
        Returns a list of fuzzy matchei to the pattern provided.
        A match is if any alias, the internal or human name
        match in lower case

        @pattern: string
        @substr: match even if substr is true
        """
        rv = []
        import operator
        if substr:
            op = operator.contains
        else:
            op = operator.eq
        pattern = pattern.lower()
        for lang in self.itervalues():
            if op(lang.internal.lower(), pattern) or \
               op(lang.human.lower(), pattern) or \
               any((op(x.lower(), pattern) for x in lang.aliases)):
                rv.append(lang)
        return rv

