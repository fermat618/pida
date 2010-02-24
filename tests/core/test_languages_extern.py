
import os
#from pida.core.doctype import DocType
#from pida.core.testing import test, assert_equal, assert_notequal
from pida.utils.languages import OutlineItem, ValidationError, Definition, \
    Suggestion, Documentation
from pida.core.languages import (Validator, Outliner, External, JobServer,
    ExternalValidatorProxy, ExternalOutlinerProxy,
    Documentator, Definer, Completer, LanguageService)
from pida.core.document import Document

from .test_services import MockBoss

from unittest import TestCase


class TestExternalValidator(Validator):

    def get_validations(self):
        yield os.getpid()
        for i in xrange(50):
            yield ValidationError(message="error %s" % i)

class TestExternalOutliner(Outliner):

    def get_outline(self):
        yield os.getpid()
        for i in xrange(50):
            yield OutlineItem(name="run %s" % i, line=i)

class TestDocumentator(Documentator):
    def get_documentation(self, buffer, offset):
        yield os.getpid()
        yield buffer
        yield offset
        for i in xrange(50):
            yield Documentation(path="run %s" % i, short="short %s" % i,
                                long=buffer[i:i + 5])

class TestCompleter(Completer):

    def get_completions(self, base, buffer, offset):
        yield os.getpid()
        yield base
        yield buffer
        yield offset
        for i in xrange(30):
            yield Suggestion("run %s" % i)


class TestDefiner(Definer):

    def get_definition(self, buffer, offset):
        yield os.getpid()
        yield buffer
        yield offset
        for i in xrange(30):
            yield Definition(line="run %s" % i, offset=i)


class MyExternal(External):
    validator = TestExternalValidator
    outliner = TestExternalOutliner
    documentator = TestDocumentator
    completer = TestCompleter
    definer = TestDefiner


class MYService(LanguageService):

    # only test if it gets overridden
    outliner_factory = TestExternalOutliner

    external = MyExternal

    def __init__(self, boss):
        LanguageService.__init__(self, boss)
        self.something = False
        self.started = False

class TestExternal(TestCase):

    def test_service(self):
        boss = MockBoss()
        svc = MYService(boss)
        svc.create_all()
        if svc.jobserver is None:
            print "Skipping external language plugins: no multiprocessing"
            return
        self.assertTrue(isinstance(svc.jobserver, JobServer))
        self.assertTrue(issubclass(svc.validator_factory,
                                   ExternalValidatorProxy))
        self.assertTrue(issubclass(svc.outliner_factory,
                                   ExternalOutlinerProxy))
        # test iterators
        doc = Document(boss, __file__)
        outliner = svc.outliner_factory(svc, doc)
        for i, v in enumerate(outliner.get_outline()):
            if i == 0:
                self.assertNotEqual(os.getpid(), v)
            else:
                self.assertTrue(isinstance(v, OutlineItem))
                self.assertEqual("run %s" % (i - 1), v.name)

        validator = svc.validator_factory(svc, doc)
        for i, v in enumerate(validator.get_validations()):
            if i == 0:
                self.assertNotEqual(os.getpid(), v)
            else:
                self.assertTrue(isinstance(v, ValidationError))
                self.assertEqual("error %s" % (i - 1), v.message)

        completer = svc.completer_factory(svc, doc)
        for i, v in enumerate(completer.get_completions('base',
                              'some text', 3)):
            if i == 0:
                self.assertNotEqual(os.getpid(), v)
            elif i == 1:
                self.assertEqual('base', v)
            elif i == 2:
                self.assertEqual('some text', v)
            elif i == 3:
                self.assertEqual(3, v)
            else:
                self.assertTrue(isinstance(v, Suggestion))
                self.assertEqual("run %s" % (i - 4), v)

        documentator = svc.documentator_factory(svc, doc)
        for i, v in enumerate(documentator.get_documentation('base',
                              'some text')):
            if i == 0:
                self.assertNotEqual(os.getpid(), v)
            elif i == 1:
                self.assertEqual('base', v)
            elif i == 2:
                self.assertEqual('some text', v)
            else:
                self.assertTrue(isinstance(v, Documentation))
                self.assertEqual("short %s" % (i - 3), v.short)
                self.assertEqual("run %s" % (i - 3), v.path)

        definer = svc.definer_factory(svc, doc)
        for i, v in enumerate(definer.get_definition('some text', 4)):
            if i == 0:
                self.assertNotEqual(os.getpid(), v)
            elif i == 1:
                self.assertEqual('some text', v)
            elif i == 2:
                self.assertEqual(4, v)
            else:
                self.assertTrue(isinstance(v, Definition))
                self.assertEqual(i - 3, v.offset)
                self.assertEqual("run %s" % (i - 3), v.line)
