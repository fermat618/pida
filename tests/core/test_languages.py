
import os
import os
#from pida.core.doctype import DocType
#from pida.core.testing import test, assert_equal, assert_notequal
from pida.core.languages import Outliner

from pida.utils.testing.mock import Mock

from unittest import TestCase
from tempfile import mktemp

class TestOutliner(Outliner):
    pass

class LanguageTest(TestCase):

    def test_uuid(self):
        self.assertEqual(TestOutliner.uuid(), 
                         'tests.core.test_languages.TestOutliner')
