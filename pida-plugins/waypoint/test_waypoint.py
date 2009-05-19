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

from pida.utils.testing.mock import Mock
from unittest import TestCase

from pida.core.document import Document

from .waypoint import WayPoint, WayStack

BOSS = Mock()

class WaypointTest(TestCase):

    def should(self, wp, should):
        for i in xrange(len(should)):
            self.assertEqual(wp[i].document, should[i][0])
            self.assertEqual(wp[i].line, should[i][1])


    def test_waypoint(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10)
        wp.notify_change(doc1, 10)
        wp.notify_change(doc1, 12)
        wp.notify_change(doc1, 15)
        wp.notify_change(doc1, 10)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 10)
        
        wp.notify_change(doc2, 100)
        self.assertEqual(wp[0].document, doc2)
        self.assertEqual(wp[0].line, 100)
        
        wp.notify_change(doc1, 100)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 100)
        
        wp.notify_change(doc1, 1)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 1)
        
        should = ((doc1, 1), (doc1, 100), (doc2, 100), (doc1, 10))
        self.should(wp, should)

    def test_waypoint_jump(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10)
        wp.notify_change(doc1, 10)
        wp.notify_change(doc1, 100)
        wp.notify_change(doc2, 100)
        wp.notify_change(doc1, 43)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 43)

        cp = wp.jump(0)
        
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 43)

        cp = wp.jump(1)
        
        self.assertEqual(cp.document, doc2)
        self.assertEqual(cp.line, 100)

        cp = wp.jump(0)
        
        self.assertEqual(cp.document, doc2)
        self.assertEqual(cp.line, 100)

        cp = wp.jump(1)
        
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 100)

        cp = wp.jump(10)
        
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 10)

        cp = wp.jump(-1)
        
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 100)

        cp = wp.jump(-2)
        
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 43)

        cp = wp.jump(1)

        self.assertEqual(cp.document, doc2)
        self.assertEqual(cp.line, 100)

        wp.notify_change(doc2, 932)

        should = ((doc2, 932), (doc2, 100), (doc1, 100), (doc1, 10))
        self.should(wp, should)

        cp = wp.jump(2)
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 100)
        
        wp.notify_change(doc1, 103)
        self.assertEqual(wp[0].document, doc2)
        self.assertEqual(wp[0].line, 932)
        self.assertEqual(wp[1].document, doc2)
        self.assertEqual(wp[1].line, 100)
        
        cp = wp.jump(-1)

        self.assertEqual(cp.document, doc2)
        self.assertEqual(cp.line, 100)


        should = ((doc2, 932), (doc2, 100), (doc1, 100), (doc1, 10))
        self.should(wp, should)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
