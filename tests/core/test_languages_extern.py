import py
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
    validator_factory = TestExternalValidator

    external = MyExternal

    def __init__(self, boss):
        LanguageService.__init__(self, boss)
        self.something = False
        self.started = False



def pytest_funcarg__svc(request):
    boss = MockBoss()
    svc = MYService(boss)
    svc.create_all()
    return svc


def pytest_funcarg__doc(request):
    svc = request.getfuncargvalue('svc')
    doc = Document(svc.boss, __file__)
    mkp = request.getfuncargvalue('monkeypatch')
    mkp.setattr(Document, 'project', None)
    doc.project = None
    return doc


def test_service_override(svc):
    assert isinstance(svc.jobserver, JobServer)
    assert issubclass(svc.validator_factory, ExternalValidatorProxy)
    assert issubclass(svc.outliner_factory, ExternalOutlinerProxy)


def test_outliner(svc, doc):
    # test iterators
    outliner = svc.outliner_factory(svc, doc)
    for i, v in enumerate(outliner.get_outline()):
        if i == 0:
            assert os.getpid() != v
        else:
            assert isinstance(v, OutlineItem)
            assert "run %s" % (i - 1) == v.name


def test_validator(svc, doc):
    validator = svc.validator_factory(svc, doc)
    for i, v in enumerate(validator.get_validations()):
        if i == 0:
            assert os.getpid() != v
        else:
            assert isinstance(v, ValidationError)
            assert "error %s" % (i - 1) == v.message


def test_completer(svc, doc):
    completer = svc.completer_factory(svc, doc)
    for i, v in enumerate(completer.get_completions('base',
                          'some text', 3)):
        if i == 0:
            assert os.getpid() != v
        elif i == 1:
            assert v == 'base'
        elif i == 2:
            assert v == 'some text'
        elif i == 3:
            assert v == 3
        else:
            assert isinstance(v, Suggestion)
            assert "run %s" % (i - 4) == v


def test_documenter(svc, doc):
    documentator = svc.documentator_factory(svc, doc)
    for i, v in enumerate(documentator.get_documentation('base',
                          'some text')):
        if i == 0:
            assert v != os.getpid()
        elif i == 1:
            assert 'base' == v
        elif i == 2:
            assert 'some text' == v
        else:
            assert isinstance(v, Documentation)
            assert "short %s" % (i - 3) == v.short
            assert "run %s" % (i - 3) == v.path


def test_definer(svc, doc):
    definer = svc.definer_factory(svc, doc)
    for i, v in enumerate(definer.get_definition('some text', 4)):
        if i == 0:
            assert os.getpid() != v
        elif i == 1:
            assert 'some text' == v
        elif i == 2:
            assert v == 4
        else:
            assert isinstance(v, Definition)
            assert i - 3 == v.offset
            assert "run %s" % (i - 3) == v.line
