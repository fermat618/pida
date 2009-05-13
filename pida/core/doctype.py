# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.doctype
    ~~~~~~~~~~~~~~~~~~

    :license: GPL2 or later
    :copyright: 2008 by The PIDA Project

"""

from glob import fnmatch


class DocType(object):
    """Represents a type of document. Like a python sourcecode file, a xml
    file, etc.
    """
    __slots__ = ('internal', 'aliases', 'human', 'extensions', 'mimes', 
                 'section', 'parsers', 'validators', 'support')

    def __init__(self, internal, human, aliases = None, extensions = None, 
                 mimes = None, section = 'Others'):
        self.internal = internal
        self.human = human
        self.aliases = aliases and list(aliases) or []
        self.extensions = extensions and list(extensions) or []
        self.mimes = mimes and list(mimes) or []
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
        return '<DocType %s %s>' %(self.internal, self.human)

class TypeManager(dict):
    """
    DocType Library
    
    This class manages a list of DocType instances and features selection
    """

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
        elif len(best_list):
            best = best_list[0]
        
        return best




