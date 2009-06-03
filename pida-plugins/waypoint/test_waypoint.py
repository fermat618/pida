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

from pida.core.document import Document

from .waypoint import WayPoint, WayStack

BOSS = Mock()

class WaypointTest(object):

    def should(self, wp, should):
        for i, (doc, pos) in enumerate(should):
            self.assertEqual(wp[i].document, doc)
            self.assertEqual(wp[i].line, pos)


    def test_has(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10, threshold=10)
        w1 = WayPoint(doc1, 10)
        w2 = WayPoint(doc1, 10)
        wp.append(w1)
        
        self.assertTrue(w1 in wp)
        self.assertTrue(w2 in wp)
        self.assertTrue(wp.has_fuzzy(w1))
        self.assertTrue(wp.has_fuzzy(w2))

        self.assertEqual(w1, wp.get_fuzzy(w1.document, w1.line+4))
        self.assertEqual(w1, wp.get_fuzzy(w1.document, w1.line+6))
        self.assertNotEqual(w1, wp.get_fuzzy(w1.document, w1.line+11))


        w3 = WayPoint(doc2, 10)
        w4 = WayPoint(doc2, 19)
        w5 = WayPoint(doc2, 20)
        w6 = WayPoint(doc2, 21)


        self.assertTrue(not w3 in wp)
        self.assertTrue(not w4 in wp)
        wp.append(w3)
        self.assertTrue(w3 in wp)
        self.assertTrue(not w4 in wp)
        self.assertTrue(wp.has_fuzzy(w3))
        self.assertTrue(wp.has_fuzzy(w4))
        self.assertTrue(not wp.has_fuzzy(w5))
        self.assertTrue(not wp.has_fuzzy(w6))

        w3 = WayPoint(doc2, 10)

    def test_maxlength(self):
        doc1 = Document(BOSS)
        wp = WayStack(max_length=10, threshold=10, timespan=5)
        for i in xrange(20):
            wp.notify_change(doc1, 100*i+1, time_=(60*i)+1)
            wp.notify_change(doc1, 100*i+1, time_=(60*i)+10)
        
        self.assertEqual(len(wp), 10)
        


    def test_waypoint(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10, threshold=30, timespan=4)
        wp.notify_change(doc1, 10, time_=10)
        wp.notify_change(doc1, 12, time_=20)
        wp.notify_change(doc1, 15, time_=40)
        wp.notify_change(doc1, 10, time_=60)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 12)
        
        wp.notify_change(doc2, 100, time_=80)
        self.assertNotEqual(wp[0].document, doc2)
        wp.notify_change(doc2, 109, time_=90)
        self.assertEqual(wp[0].document, doc2)
        print wp
        print wp._considered
        self.assertEqual(wp[0].line, 109)
        
        wp.notify_change(doc1, 100, time_=100)
        self.assertNotEqual(wp[0].document, doc1)
        wp.notify_change(doc1, 100, time_=104)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 100)

        # this will not generate a new waypoint as its to near on the first one
        wp.notify_change(doc1, 1, time_=120)
        wp.notify_change(doc1, 1, time_=125)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 100)

        # this will
        wp.notify_change(doc1, 50, time_=140)
        wp.notify_change(doc1, 50, time_=150)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 50)

        
        should = ((doc1, 50), (doc1, 100), (doc2, 109), (doc1, 12))
        self.should(wp, should)

    def test_force(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10)
        wp.notify_change(doc1, 10, time_=10)
        wp.notify_change(doc1, 10, time_=20)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 10)
        wp.notify_change(doc1, 15, time_=22, force=True)
        self.assertEqual(wp[0].document, doc1)
        self.assertEqual(wp[0].line, 15)
        self.assertEqual(wp[1].document, doc1)
        self.assertEqual(wp[1].line, 10)
        wp.notify_change(doc2, 1, time_=32, force=True)
        wp.notify_change(doc1, 15, time_=32, force=True)
        self.assertEqual(wp[0].document, doc2)
        self.assertEqual(wp[0].line, 1)
        self.assertEqual(wp[1].document, doc1)
        self.assertEqual(wp[1].line, 15)


    def test_waypoint_jump(self):
        doc1 = Document(BOSS)
        doc2 = Document(BOSS)
        wp = WayStack(max_length=10)
        wp.notify_change(doc1, 10, time_=10)
        wp.notify_change(doc1, 10, time_=20)
        wp.notify_change(doc1, 100, time_=30)
        wp.notify_change(doc1, 100, time_=40)
        wp.notify_change(doc2, 100, time_=50)
        wp.notify_change(doc2, 100, time_=60)
        wp.notify_change(doc1, 43, time_=70)
        wp.notify_change(doc1, 43, time_=80)
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

        wp.notify_change(doc2, 930, time_=100)
        wp.notify_change(doc2, 932, time_=110)

        should = ((doc2, 932), (doc2, 100), (doc1, 100), (doc1, 10))
        self.should(wp, should)

        cp = wp.jump(2)
        self.assertEqual(cp.document, doc1)
        self.assertEqual(cp.line, 100)
        
        wp.notify_change(doc1, 103, time_=120)
        wp.notify_change(doc1, 103, time_=130)
        
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
