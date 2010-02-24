
from pida.core.doctype import DocType, TypeManager
#from pida.core.testing import test, assert_equal, assert_notequal

#from pida.utils.testing.mock import Mock

from unittest import TestCase

class TestParser(object):
    pass

class DoctypeTest(TestCase):

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

    def test_fuzzy_list(self):
        self.build_doctypes()
        self.assertEqual(self.doctypes.get_fuzzy_list('C'), [self.doctypes['C']])
        self.assertEqual(self.doctypes.get_fuzzy_list('Cpp'), [self.doctypes['Cpp']])
        self.assertEqual(self.doctypes.get_fuzzy_list('C'), [self.doctypes['C']])
        self.assertEqual(self.doctypes.get_fuzzy_list('pyThoN'),
                         [self.doctypes['Python']])
        self.assertEqual(self.doctypes.get_fuzzy_list('py', True),
                         [self.doctypes['PythonConsole'],
                         self.doctypes['PythonTraceback'],
                         self.doctypes['Python']])

    def test_filename(self):
        self.build_doctypes()
        self.assertEqual(self.doctypes.type_by_filename('source.c'),
                         self.doctypes['C'])
        self.assertEqual(self.doctypes.type_by_filename('source.h'),
                         self.doctypes['C'])
        self.assertEqual(self.doctypes.type_by_filename('source.cpp'),
                         self.doctypes['Cpp'])
        self.assertEqual(self.doctypes.type_by_filename('LICENSE'),
                         None)
        self.assertEqual(self.doctypes.type_by_filename('some.tk'),
                         self.doctypes['Tcl'])
        self.assertEqual(self.doctypes.type_by_filename('some.tcl'),
                         self.doctypes['Tcl'])
        self.assertEqual(self.doctypes.type_by_filename('some.c.tcl'),
                         self.doctypes['Tcl'])
        self.assertEqual(self.doctypes.type_by_filename('sources.list'),
                         self.doctypes['SourcesList'])
        self.assertEqual(self.doctypes.type_by_filename('1sources.list'),
                         None)
        self.assertEqual(self.doctypes.type_by_filename('sources.list_'),
                         None)
        self.assertEqual(self.doctypes.type_by_filename('makefile.am'),
                         self.doctypes['Makefile'])
        self.assertEqual(self.doctypes.type_by_filename('Makefile'),
                         self.doctypes['Makefile'])
        self.assertEqual(self.doctypes.type_by_filename('Makefile.in'),
                         self.doctypes['Makefile'])
