
from simplejson import dumps

from ..model import Build, dump
from ..execute import generate_execution_graph, CircularAction, execute_build

t = dict(
    targets = [
        dict(
            name = 'test',
            actions = [
                dict(type='shell',value='echo 123', options={})
            ],
        ),
        dict(
            name = 'test2',
            actions = [
                dict(type='shell',value='blah', options={}),
                dict(type='target',value='test3', options={})
            ],
        ),
        dict(
            name = 'test3',
            actions = [
                dict(type='shell',value='blah', options={}),
                dict(type='target',value='test2', options={})
            ],
        ),
        dict(
            name = 'test4',
            actions = [
                dict(type='target',value='test5', options={})
            ],
        ),
        dict(
            name = 'test5',
            actions = [
                dict(type='shell',value='echo hello', options={}),
            ],
        ),
        dict(
            name = 'test6',
            actions = [
                dict(type='python',value='print "byebye"', options={}),
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

def _target_test(name='test'):
    def _decorator(f):
        b, j = _get_test_build()
        t = b.targets[0]
        def _f():
            return f(t)
        _f.__name__ = f.__name__
        return _f
    return _decorator



def _action_test(f):
    b, j = _get_test_build()
    t = b.targets[0]
    a = t.actions[0]
    def _f():
        return f(a)
    _f.__name__ = f.__name__
    return _f


def _graph_test(target_name='test'):
    def _decorator(f):
        b, j = _get_test_build()
        g = generate_execution_graph(b, target_name)
        def _f():
            return f(g)
        _f.__name__ = f.__name__
        return _f
    return _decorator


def _execution_result_test(target_name='test'):
    def _decorator(f):
        b, j = _get_test_build()
        res = list(execute_build(b, target_name))
        def _f():
            return f(res)
        _f.__name__ = f.__name__
        return _f
    return _decorator


@_build_test
def test_targets(b):
    assert len(b.targets) == len(t['targets'])


@_target_test()
def test_target_name(t):
    assert t.name == 'test'


@_target_test()
def test_target_actions(t):
    assert(len(t.actions) == 1)


@_target_test()
def test_target_serialise(t):
    assert t.for_serialize() == {'name':u'test',
        'actions':[{'type':u'shell','value':u'echo 123','options':{}}]}


@_action_test
def test_action_type(a):
    assert a.type == 'shell'


@_action_test
def test_action_value(a):
    assert a.value == 'echo 123'


@_action_test
def test_action_options(a):
    assert a.options == {}


@_action_test
def test_action_serialize(a):
    assert a.for_serialize() == {'type':u'shell','value':u'echo 123','options':{}}


@_build_test
def test_create_graph(b):
    root = generate_execution_graph(b, 'test')
    assert len(root.children) == 1
    assert len(root.actions) == 1


@_graph_test()
def test_simple_children(g):
    assert len(g.children) == 1


@_graph_test()
def test_simple_actions(g):
    assert len(g.actions) == 1


@_graph_test('test4')
def test_dependency(g):
    assert len(g.children) == 1


@_graph_test('test4')
def test_dependency_children(g):
    assert len(g.children[0].children) == 1


@_graph_test('test4')
def test_dependency_target(g):
    assert g.children[0].target.name == 'test5'


@_graph_test('test4')
def test_dependency_actions(g):
    assert len(g.actions) == 1


@_graph_test('test2')
def test_circular_graph(g):
    assert g.children[1].children[1].circular


@_graph_test('test2')
def test_circular_nochildren(g):
    assert not g.children[1].children[1].children


@_graph_test('test2')
def test_circular_actions(g):
    assert len(g.actions) == 3


@_graph_test('test2')
def test_circular_flag_action(g):
    assert isinstance(g.actions[2], CircularAction)


@_build_test
def test_execute_shell(b):
    res = list(execute_build(b, 'test'))
    assert res[0] == '123\n'


@_execution_result_test('test5')
def test_execute_shell_result(res):
    assert res[0] == 'hello\n'


@_execution_result_test('test4')
def test_execute_circular_result(res):
    assert res[0] == 'hello\n'


@_execution_result_test('test6')
def test_execute_python_result(res):
    assert res[0] == 'byebye\n'

