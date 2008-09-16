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




