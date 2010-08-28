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

import unittest
from ctags import CtagsOutliner, build_language_list
from pida.core.document import Document
import os

TESTDIR = os.path.join(os.path.dirname(__file__), 'test')

from pida.utils.testing.mock import Mock

class TestCtags(unittest.TestCase):
    def test_parser(self):
        self.doc = Document(None, os.path.join(TESTDIR, 'test.py'))
        self.outliner = CtagsOutliner(None, document=self.doc)
        lst = list(self.outliner.get_outline())
        outer = None
        inner = None
        for x in lst:
            if x.name == "Outer":
                outer = x
            elif x.name == "Inner":
                inner = x
        self.assert_(outer)
        self.assertEqual(outer.parent, None)
        self.assertEqual(inner.parent, outer)
        for x in lst:
            if x.name[:6] == "outer_":
                self.assertEqual(x.parent, outer)
            if x.name[:6] == "inner_":
                self.assertEqual(x.parent, inner)
            #print x

    def test_languagemap(self):
        from pida.core.doctype import TypeManager
        doctypes = TypeManager()
        from pida.services.language import deflang
        doctypes._parse_map(deflang.DEFMAPPING)
        lst = build_language_list(doctypes)
        if len(lst) == 0:
            #FIXME: no ctags i guess, should be tested
            return 
        # those should be in the ctags
        self.assertTrue(all([x in doctypes.values() for x in lst]))
        self.assertTrue(len(lst) > 10)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
