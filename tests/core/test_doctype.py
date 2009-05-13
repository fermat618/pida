
from pida.core.doctype import DocType, TypeManager
#from pida.core.testing import test, assert_equal, assert_notequal

#from pida.utils.testing.mock import Mock

from unittest import TestCase

class TestParser(object):
    pass

class DocumentTest(TestCase):

    def build_doctypes(self):
        #self.assertEqual(_DEFMAPPING.keys().sort(), Manager.keys().sort())
        self.doctypes = TypeManager()
        from pida.services.language import deflang
        self.doctypes._parse_map(deflang.DEFMAPPING)


    def test_new_doctype(self):
        self.assertRaises(TypeError, DocType)
        doc = DocType('test', 'Some Test')
        self.assertEqual(doc.human, 'Some Test')
        self.assertEqual(doc.internal, 'test')
        self.assertEqual(unicode(doc), doc.human)

    def test_def_manager(self):
        self.build_doctypes()
        # there should be at least 120 doctypes already defined
        self.assertTrue(len(self.doctypes) > 120)
        # test for the existenze of some importen once
        self.assertTrue(all([x in self.doctypes for x in (
                            'Python', 'Lua', 'Diff', 'Cpp', 'Html')]))

    def test_fuzzy(self):
        self.build_doctypes()
        self.assertEqual(self.doctypes.get_fuzzy('C++'), self.doctypes['Cpp'])
        self.assertEqual(self.doctypes.get_fuzzy('Cpp'), self.doctypes['Cpp'])
        self.assertEqual(self.doctypes.get_fuzzy('C'), self.doctypes['C'])
        self.assertEqual(self.doctypes.get_fuzzy('pyThoN'),
                         self.doctypes['Python'])
        self.assertEqual(self.doctypes.get_fuzzy('XML+django/jinja'),
                         self.doctypes['XmlDjango'])
        self.assertEqual(self.doctypes.get_fuzzy('XML+jinja'),
                         self.doctypes['XmlDjango'])
        self.assertEqual(self.doctypes.get_fuzzy('xml+dJanGo'),
                         self.doctypes['XmlDjango'])
