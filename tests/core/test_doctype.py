
import os
import os
from pida.core.doctype import DocType
#from pida.core.testing import test, assert_equal, assert_notequal

from pida.utils.testing.mock import Mock

from unittest import TestCase
from tempfile import mktemp

class TestParser(object):
    pass

class DocumentTest(TestCase):

    def test_new_doctype(self):
        self.assertRaises(TypeError, DocType)
        doc = DocType('test', 'Some Test')
        self.assertEqual(doc.human, 'Some Test')
        self.assertEqual(doc.internal, 'test')
        self.assertEqual(unicode(doc), doc.human)

    def test_def_manager(self):
        #self.assertEqual(_DEFMAPPING.keys().sort(), Manager.keys().sort())
        pass
        
