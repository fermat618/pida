
import os
from pida.core.document import Document as document_class
from pida.core.document import DocumentException
#from pida.core.testing import test, assert_equal, assert_notequal

from pida.utils.testing.mock import Mock

from unittest import TestCase
from tempfile import mktemp

def document(*k, **kw):
    mock = Mock()
    mock.boss.cmd().return_value = None
    return document_class(None, *k, **kw)

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



def test_new_document():
    doc = document()
    assert doc.is_new

def test_unnamed_document():
    doc = document()
    assert doc.filename is None

def test_new_index():
    doc = document()
    doc2 = document()
    assert doc.newfile_index != doc2.newfile_index

def test_no_project():
    doc = document()
    assert doc.project_name == ''

def test_unique_id():
    doc = document()
    doc2 = document()
    assert doc.unique_id != doc2.unique_id

def test_real_file():
    doc, tmp, txt = c()
    assert doc.filename == tmp
    d(tmp)

def test_file_text():
    doc, tmp, txt = c()
    assert doc.content == txt
    d(tmp)

def test_file_lines():
    doc, tmp, txt = c()
    assert len(doc.lines) == 2
    d(tmp)

def test_file_len():
    doc, tmp, txt = c()
    assert doc.filesize == len(txt)
    d(tmp)

def test_directory():
    doc, tmp, txt = c()
    assert doc.directory == '/tmp'
    d(tmp)


def test_directory_basename():
    doc, tmp, txt = c()
    assert doc.directory_basename, 'tmp'
    d(tmp)


def test_basename():
    doc, tmp, txt = c()
    assert doc.basename == os.path.basename(tmp)
    d(tmp)

def test_file_missing_load():
    doc = document(filename='/this_is_hopefully_missing_for_sure')
    doc._load()

def test_file_missing_stat():
    doc = document(filename='/this_is_hopefully_missing_for_sure')
    assert doc.stat == (0,)*10

def test_repr_new():
    from pida.core import document as document_module
    doc = document()
    rep = repr(doc)
    expected = '<New Document %d (%s)>' % (
            document_module.new_file_index-1, id(doc))
    assert rep == expected

def test_repr_known():
    doc = document(filename='test')
    expected = "<Document '%s' (%s)>" % (os.path.abspath('test'), id(doc))
    assert repr(doc) == expected
    
def test_unicode_new():
    from pida.core import document as document_module
    doc = document()
    assert unicode(doc) == u'Untitled (%d)' %(document_module.new_file_index-1)

def test_unicode_knows():
    doc = document(filename='test')
    assert unicode(doc) == doc.basename
    
def test_content_nonlife(tmpdir):
    tempfile = tmpdir.ensure('foo')
    name = str(tempfile)
    d = document(filename=name)
    STR1 = u'i write something'
    STR2 = u'other text too'
    d.content = STR1
    assert d.content == STR1
    del d
    d = document(filename=name)
    assert d.content == STR1
    d.content = STR2
    assert d.content == STR2
    d.content += STR1
    assert d.content == "%s%s" %(STR2, STR1)
    del d
    d = document(filename=name)
    assert d.content == "%s%s" %(STR2, STR1)
    os.unlink(name)

