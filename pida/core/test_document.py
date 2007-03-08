
import os

from pida.core.document import document
#from pida.core.testing import test, assert_equal, assert_notequal

from unittest import TestCase

def c():
    tmp = os.popen('tempfile').read().strip()
    f = open(tmp, 'w')
    txt ="""Hello I am a document
               vlah blah"""
    f.write(txt)
    f.close()
    doc = document(filename=tmp)
    return doc, tmp, txt

def d(tmp):
    os.system('rm %s' % tmp)

class DocumentTest(TestCase):

    def test_new_document(self):
        doc = document()
        self.assertEqual(doc.is_new, True)

    def test_unnamed_document(self):
        doc = document()
        self.assertEqual(doc.filename, None)

    def test_unnamed_is_new(self):
        doc = document()
        self.assertEqual(doc.is_new, True)
        self.assertEqual(doc.filename, None)

    def test_new_index(self):
        doc = document()
        doc2 = document()
        self.assertNotEqual(doc.newfile_index, doc2.newfile_index)

    def test_no_project(self):
        doc = document()
        self.assertEqual(doc.project_name, '')

    def test_no_handler(self):
        doc = document()
        self.assertEqual(doc.handler, None)


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
        self.assertEqual(doc.string, txt)
        d(tmp)

    def test_file_lines(self):
        doc, tmp, txt = c()
        self.assertEqual(len(doc.lines), 2)
        d(tmp)

    def test_file_len(self):
        doc, tmp, txt = c()
        self.assertEqual(len(doc), len(txt))
        d(tmp)

    def test_file_length(self):
        doc, tmp, txt = c()
        self.assertEqual(doc.length, len(doc))
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


