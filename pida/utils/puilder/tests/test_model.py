
from simplejson import dumps

from ..model import Build, dump


t = dict(
    targets = [
        dict(
            name = 'test',
            actions = [
                dict(type='shell',value='blah', options={})
            ],
        )
    ],
    options = {}
)

def _get_test_build():
    json = dumps(t, sort_keys=False, indent=2)
    return Build.loads(json), json


def _build_test(f):
    b, j = _get_test_build()
    def _f():
        return f(b)
    _f.__name__ = f.__name__
    return _f


def _target_test(f):
    b, j = _get_test_build()
    t = b.targets[0]
    def _f():
        return f(t)
    _f.__name__ = f.__name__
    return _f


def _action_test(f):
    b, j = _get_test_build()
    t = b.targets[0]
    a = t.actions[0]
    def _f():
        return f(a)
    _f.__name__ = f.__name__
    return _f


@_build_test
def test_targets(b):
    assert len(b.targets) == 1


@_target_test
def test_target_name(t):
    assert t.name == 'test'


@_target_test
def test_target_actions(t):
    assert(len(t.actions) == 1)


@_target_test
def test_target_serialise(t):
    assert t.for_serialize() == {'name':u'test',
        'actions':[{'type':u'shell','value':u'blah','options':{}}]}


@_action_test
def test_action_type(a):
    assert a.type == 'shell'


@_action_test
def test_action_value(a):
    assert a.value == 'blah'


@_action_test
def test_action_options(a):
    assert a.options == {}


@_action_test
def test_action_serialize(a):
    assert a.for_serialize() == {'type':u'shell','value':u'blah','options':{}}

