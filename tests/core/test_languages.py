
#from pida.core.doctype import DocType
#from pida.core.testing import test, assert_equal, assert_notequal
from pida.core.languages import Outliner
from pida.services.language.language import (CustomLanguageMapping,
    CustomLanguagePrioList, LanguageService)
from pida.services.language import DOCTYPES
from pida.services.language.disabled import NoopOutliner

from .test_services import MockBoss

from unittest import TestCase

class TestOutliner(Outliner):
    priority = 10

class TestOutliner2(Outliner):
    priority = 20

class TestOutliner3(Outliner):
    priority = 30

class TestOutliner4(Outliner):
    priority = 0

class TestOutlinerUp(Outliner):
    pass

MOCKBOSS = MockBoss()
TEST_SERVICE = LanguageService(MOCKBOSS)
TEST_SERVICE.doctypes = DOCTYPES


class PriorityTest(TestCase):

    default_sort_list = {'test': [
                            {'description': 'DESCRIPTION MISSING',
                             'plugin': 'PLUGIN MISSING',
                             'uuid': 'tests.core.test_languages.TestOutliner2',
                             'name': 'NAME MISSING'},
                            {'description': 'DESCRIPTION MISSING',
                             'plugin': 'PLUGIN MISSING',
                             'uuid': 'tests.core.test_languages.TestOutliner',
                             'name': 'NAME MISSING'},
                            {'description': 'DESCRIPTION MISSING',
                             'plugin': 'PLUGIN MISSING',
                             'uuid': 'tests.core.test_languages.TestOutliner3',
                             'name': 'NAME MISSING'}]}

    def test_priority(self):
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm.add('test', TestOutliner2)
        lm.add('test', TestOutliner)
        lm.add('test', TestOutliner2)
        lm.add('test', TestOutliner3)
        # it's not customized yet, so it's not empty
        self.assertEqual(lm.dump(), {})
        print lm['test']
        self.assertEqual(lm['test'],
            [TestOutliner3, TestOutliner2, TestOutliner])
        lm['test'].customized = True
        lm['test'].update_sort_list()
        self.assertEqual(lm.dump(),
            {'test':   [{'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner3',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner2',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner',
                         'name': 'NAME MISSING'}]})

    def test_load(self):
        lm = CustomLanguageMapping(TEST_SERVICE)
        sort_list = {'test': [
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner3',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner2',
                         'name': 'NAME MISSING'}]}
        lm.load(sort_list)
        lm.add('test', TestOutliner2)
        self.assertEqual(lm['test'],
            [TestOutliner2])
        self.assertEqual(lm.dump(), sort_list)

        lm.add('test', TestOutliner)
        self.assertEqual(lm['test'],
            [TestOutliner, TestOutliner2])
        self.assertEqual(lm.dump(), sort_list)

        lm.add('test', TestOutliner3)
        self.assertEqual(lm['test'],
            [TestOutliner3, TestOutliner, TestOutliner2])
        self.assertEqual(lm.dump(), sort_list)

        lm.add('test2', TestOutliner)
        lm.add('test2', TestOutliner)
        lm.add('test2', TestOutliner3)
        self.assertEqual(lm.dump(), sort_list)

    def test_def_priority(self):
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm.add('test', TestOutliner4)
        lm.add('test', TestOutliner2)
        lm.add('test', NoopOutliner)
        self.assertEqual(lm, {'test':
                              [TestOutliner2, TestOutliner4, NoopOutliner]})
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm.add('test', NoopOutliner)
        lm.add('test', TestOutliner2)
        lm.add('test', TestOutliner4)
        self.assertEqual(lm, {'test':
                              [TestOutliner2, TestOutliner4, NoopOutliner]})

    def test_movement(self):
        sort_list = {'test': [
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner3',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner',
                         'name': 'NAME MISSING'},
                        {'description': 'DESCRIPTION MISSING',
                         'plugin': 'PLUGIN MISSING',
                         'uuid': 'tests.core.test_languages.TestOutliner2',
                         'name': 'NAME MISSING'}]}
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm['test'] = CustomLanguagePrioList(sort_list=sort_list['test'])
        lm.add('test', TestOutliner4)
        lm.add('test', TestOutliner2)
        lm.add('test', NoopOutliner)
        lm.add('test', TestOutliner)
        lm.add('test', TestOutliner3)
        self.assertEqual(lm, {'test':
                              [TestOutliner3, TestOutliner, TestOutliner2,
                              TestOutliner4, NoopOutliner]})
        lm['test'].replace([TestOutliner4, NoopOutliner, TestOutliner])
        lm['test'].update_sort_list()
        self.assertEqual(lm, {'test':
                              [TestOutliner4, NoopOutliner, TestOutliner]})
        self.assertEqual(lm.dump(),
                {'test':
                    [{'description': 'DESCRIPTION MISSING',
                      'plugin': 'PLUGIN MISSING',
                      'uuid': 'tests.core.test_languages.TestOutliner4',
                      'name': 'NAME MISSING'},
                     {'description': 'Disables the functionality',
                      'plugin': 'language',
                      'uuid': 'pida.services.language.disabled.NoopOutliner',
                      'name': 'Disabled'},
                     {'description': 'DESCRIPTION MISSING',
                      'plugin': 'PLUGIN MISSING',
                      'uuid': 'tests.core.test_languages.TestOutliner',
                      'name': 'NAME MISSING'}]})

    def test_update(self):
        sort_list = [{
            'description': 'DESCRIPTION MISSING',
            'plugin': 'PLUGIN MISSING',
            'uuid': 'tests.core.test_languages.TestOutlinerUp',
            'name': 'NAME MISSING',
            }]
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm.add('test', TestOutlinerUp)
        lm['test'].set_sort_list(sort_list)
        TestOutlinerUp.name = "TestUP"
        TestOutlinerUp.description = "Somedesc"
        TestOutlinerUp.plugin = "langtest"
        self.assertEqual(lm.dump(),
                {'test':
                    [{'description': 'Somedesc',
                      'plugin': 'langtest',
                      'uuid': 'tests.core.test_languages.TestOutlinerUp',
                      'name': 'TestUP'
                    }]
                })

    def test_best(self):
        lm = CustomLanguageMapping(TEST_SERVICE)
        lm.load(self.default_sort_list)
        #ltest = lm.get_or_create('test')
        lm.add('test', TestOutliner3)
        self.assertEqual(lm.get_best('test'), TestOutliner3)
        lm.add(None, TestOutliner)
        self.assertEqual(lm.get_best('test'), TestOutliner)
        lm.add(None, TestOutliner2)
        self.assertEqual(lm.get_best('test'), TestOutliner2)
        self.assertEqual(lm.get_best(None), TestOutliner2)


class LanguageTest(TestCase):

    def test_uuid(self):
        self.assertEqual(TestOutliner.uuid(),
                         'tests.core.test_languages.TestOutliner')
        self.assertEqual(TestOutliner2.uuid(),
                         'tests.core.test_languages.TestOutliner2')

