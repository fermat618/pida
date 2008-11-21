
import os
from pida.core.document import Document as document_class
from pida.core.document import DocumentException
#from pida.core.testing import test, assert_equal, assert_notequal

from pida.utils.testing.mock import Mock

from unittest import TestCase
from tempfile import mktemp

def document(*k, **kw):
    mock = Mock()
    mock.log = Mock()
    return document_class(mock, *k, **kw)

def c():
    tmp = mktemp()
    f = open(tmp, 'w')
    txt ="""Hello I am a document
               vlah blah"""
    f.write(txt)
    f.close()
    doc = document(filename=tmp)
    return doc, tmp, txt

def d(x):
    os.remove(x)


class DocumentTest(TestCase):

    def test_new_document(self):
        doc = document()
        self.assertEqual(doc.is_new, True)
        self.assertEqual(doc.filename, None)

    def test_unnamed_document(self):
        doc = document()
        self.assertEqual(doc.filename, None)


    def test_new_index(self):
        doc = document()
        doc2 = document()
        self.assertNotEqual(doc.newfile_index, doc2.newfile_index)

    def test_no_project(self):
        doc = document()
        self.assertEqual(doc.project_name, '')

    def test_unique_id(self):
        doc = document()
        doc2 = document()
        self.assertNotEqual(doc.unique_id, doc2.unique_id)

    def test_real_file(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.filename, tmp)
        d(tmp)

    def test_file_text(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.content, txt)
        d(tmp)

    def test_file_lines(self):
        doc, tmp, txt = c()
        self.assertEqual(len(doc.lines), 2)
        d(tmp)

    def test_file_len(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.filesize, len(txt))
        d(tmp)

    def test_directory(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.directory, '/tmp')
        d(tmp)


    def test_directory_basename(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.directory_basename, 'tmp')
        d(tmp)


    def test_basename(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.basename, os.path.basename(tmp))
        d(tmp)

    def test_file_missing_load(self):
        doc = document(filename='/this_is_hopefully_missing_for_sure')
        doc._load()

    def test_file_missing_stat(self):
        doc = document(filename='/this_is_hopefully_missing_for_sure')
        self.assertEqual(doc.stat, (0,)*10)

    def test_repr_new(self):
        from pida.core import document as document_module
        doc = document()
        self.assertEqual(repr(doc), '<New Document %d (%s)>'%(document_module.new_file_index-1, id(doc)))

    def test_repr_known(self):
        doc = document(filename='test')
        self.assertEqual(repr(doc), "<Document '%s' (%s)>" %
                                    (os.path.abspath('test'), id(doc)))
        
    def test_unicode_new(self):
        from pida.core import document as document_module
        doc = document()
        self.assertEqual(unicode(doc), u'Untitled (%d)' %(document_module.new_file_index-1))
    
    def test_unicode_knows(self):
        doc = document(filename='test')
        self.assertEqual(unicode(doc), doc.basename)
        
    def test_content_nonlife(self):
        import tempfile
        name = tempfile.mkstemp(suffix="pida-test")[1]
        d = document(filename=name)
        STR1 = u'i write something'
        STR2 = u'other text too'
        d.content = STR1
        self.assertEqual(d.content, STR1)
        del d
        d = document(filename=name)
        self.assertEqual(d.content, STR1)
        d.content = STR2
        self.assertEqual(d.content, STR2)
        d.content += STR1
        self.assertEqual(d.content, "%s%s" %(STR2, STR1))
        del d
        d = document(filename=name)
        self.assertEqual(d.content, "%s%s" %(STR2, STR1))
        os.unlink(name)

