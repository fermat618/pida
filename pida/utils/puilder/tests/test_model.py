
from simplejson import dumps

from pida.utils.testing import refresh_gui

from ..model import Build, dump
from ..execute import generate_execution_graph, CircularAction, execute_build
from ..view import PuilderView, TargetActionView, ShellActionView, \
                   PythonActionView, ExternalActionView

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


@_action_test
def test_shell_action_view_command(a):
    v = ShellActionView()
    v._set_action(a)
    refresh_gui()
    v.command.set_text('echo 456')
    refresh_gui()
    assert a.value == 'echo 456'


@_action_test
def test_shell_action_view_cwd(a):
    v = ShellActionView()
    v._set_action(a)
    refresh_gui()
    v.cwd_on.set_active(True)
    assert a.options == {'cwd':v.cwd.get_current_folder()}


@_action_test
def test_python_action_view(a):
    v = PythonActionView()
    v._set_action(a)
    refresh_gui()
    v.text.get_buffer().set_text('print 1')
    refresh_gui()
    assert a.value == 'print 1'


@_build_test
def test_main_view_targets(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert len(v.targets_list) == len(b.targets)
    assert list(v.targets_list) == list(b.targets)


@_build_test
def test_main_view_actions(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert list(v.acts_list) == v.targets_list[0].actions


@_build_test
def test_main_view_actions(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    v.targets_list.select(v.targets_list[1])
    refresh_gui()
    assert list(v.acts_list) == v.targets_list[1].actions


@_build_test
def test_main_view_add_action(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert list(v.acts_list) == v.targets_list[0].actions
    t = len(v.acts_list)
    v.AddActs.activate()
    refresh_gui()
    assert len(v.acts_list) > t
    assert v.acts_list[-1].value == ''
    assert v.acts_list[-1].type == 'shell'
    assert v.acts_list[-1] in v.targets_list.get_selected().actions


@_build_test
def test_main_view_add_target(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert len(v.targets_list) == len(b.targets)
    t = len(v.targets_list)
    v.AddTarget.activate()
    refresh_gui()
    assert len(v.targets_list) > t
    assert v.targets_list[-1] in b.targets
    assert v.targets_list[-1].actions == []


@_build_test
def test_main_view_add_target_shell(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert len(v.targets_list) == len(b.targets)
    t = len(v.targets_list)
    v.AddShellTarget.activate()
    refresh_gui()
    assert len(v.targets_list) > t
    assert v.targets_list[-1] in b.targets
    assert v.targets_list[-1].actions == b.targets[-1].actions
    assert b.targets[-1].actions[0].type == 'shell'


@_build_test
def test_main_view_add_target_shell(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert len(v.targets_list) == len(b.targets)
    t = len(v.targets_list)
    v.AddPythonTarget.activate()
    refresh_gui()
    assert len(v.targets_list) > t
    assert v.targets_list[-1] in b.targets
    assert v.targets_list[-1].actions == b.targets[-1].actions
    assert b.targets[-1].actions[0].type == 'python'



@_build_test
def test_main_view_action_view(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    act = v.acts_list.get_selected()
    shouldbe = v.acts_holder.page_num(v.action_views[act.type].get_toplevel())
    assert shouldbe == v.acts_holder.get_current_page()


@_build_test
def test_main_view_select_action(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    v.targets_list.select(v.targets_list[1])
    v.acts_list.select(v.acts_list[1])
    refresh_gui()
    shouldbe = v.acts_holder.page_num(v.action_views['target'].get_toplevel())
    assert shouldbe == v.acts_holder.get_current_page()

