
import py
from pida.utils.serialize import dumps

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
                dict(type='shell',value='echo 123', options={}),
                dict(type='shell',value='echo 234', options={})
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

def pytest_funcarg__json(request):
    json = dumps(t, sort_keys=False, indent=2)

def pytest_funcarg__b(request):
    json = dumps(t, sort_keys=False, indent=2)
    return Build.loads(json)

def pytest_funcarg__t(request):
    b = request.getfuncargvalue('b')
    return b.targets[0]

def pytest_funcarg__a(request):
    t = request.getfuncargvalue('t')
    return t.actions[0]

def target_or_test(function):
    if hasattr(function, 'target'):
        return function.target.args[0]
    else:
        return 'test'

def pytest_funcarg__g(request):
    b = request.getfuncargvalue('b')
    return generate_execution_graph(b, target_or_test(request.function))

def pytest_funcarg__res(request):
    b = request.getfuncargvalue('b')
    target = target_or_test(request.function)
    return list(execute_build(b, target))


def test_targets(b):
    assert len(b.targets) == len(t['targets'])

def test_target_name(t):
    assert t.name == 'test'

def test_target_actions(t):
    assert(len(t.actions) == 2)

def test_target_serialise(t):
    assert t.for_serialize() == {'name':u'test',
        'actions':[
            {'type':u'shell','value':u'echo 123','options':{}},
            {'type':u'shell','value':u'echo 234','options':{}},
        ]}

def test_action_type(a):
    assert a.type == 'shell'

def test_action_value(a):
    assert a.value == 'echo 123'

def test_action_options(a):
    assert a.options == {}

def test_action_serialize(a):
    assert a.for_serialize() == {'type':u'shell','value':u'echo 123','options':{}}

def test_create_graph(b):
    root = generate_execution_graph(b, 'test')
    assert len(root.children) == 2
    assert len(root.actions) == 2


def test_simple_children(g):
    assert len(g.children) == 2


def test_simple_actions(g):
    assert len(g.actions) == 2


@py.test.mark.target('test4')
def test_dependency(g):
    assert len(g.children) == 1


@py.test.mark.target('test4')
def test_dependency_children(g):
    assert len(g.children[0].children) == 1


@py.test.mark.target('test4')
def test_dependency_target(g):
    assert g.children[0].target.name == 'test5'


@py.test.mark.target('test4')
def test_dependency_actions(g):
    assert len(g.actions) == 1


@py.test.mark.target('test2')
def test_circular_graph(g):
    assert g.children[1].children[1].circular


@py.test.mark.target('test2')
def test_circular_nochildren(g):
    assert not g.children[1].children[1].children


@py.test.mark.target('test2')
def test_circular_actions(g):
    assert len(g.actions) == 3


@py.test.mark.target('test2')
def test_circular_flag_action(g):
    assert isinstance(g.actions[2], CircularAction)


def test_execute_shell(b):
    res = list(execute_build(b, 'test'))
    assert res[0].getvalue() == '123\n'


@py.test.mark.target('test5')
def test_execute_shell_result(res):
    assert res[0].getvalue() == 'hello\n'


@py.test.mark.target('test4')
def test_execute_circular_result(res):
    assert res[0].getvalue() == 'hello\n'


@py.test.mark.target('test6')
def test_execute_python_result(res):
    assert res[0] == 'byebye\n'


def test_shell_action_view_command(a):
    v = ShellActionView()
    v._set_action(a)
    refresh_gui()
    v.command.set_text('echo 456')
    refresh_gui()
    assert a.value == 'echo 456'


def test_shell_action_view_cwd(a):
    v = ShellActionView()
    v._set_action(a)
    refresh_gui()
    v.cwd_on.set_active(True)
    assert a.options == {'cwd':v.cwd.get_current_folder()}


def test_python_action_view(a):
    v = PythonActionView()
    v._set_action(a)
    refresh_gui()
    v.text.get_buffer().set_text('print 1')
    refresh_gui()
    assert a.value == 'print 1'


def test_main_view_targets(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert len(v.targets_list) == len(b.targets)
    assert list(v.targets_list) == list(b.targets)


def test_main_view_set_build(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    assert list(v.acts_list) == v.targets_list[0].actions


def test_main_view_actions(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    v.targets_list.selected_item = v.targets_list[1]
    refresh_gui()
    print list(v.acts_list)
    print v.targets_list[1].actions
    assert list(v.acts_list) == v.targets_list[1].actions


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
    assert v.acts_list[-1] in v.targets_list.selected_item.actions


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


def test_main_view_add_target_python(b):
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



def test_main_view_action_view(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    act = v.acts_list.selected_item
    shouldbe = v.acts_holder.page_num(v.action_views[act.type].widget)
    assert shouldbe == v.acts_holder.get_current_page()


def test_main_view_switch_to_action(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    v.proxy.update('test1')


def test_main_view_select_action(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    print list(v.targets_list)
    v.targets_list.selected_item = v.targets_list[1]
    refresh_gui()
    print list(v.acts_list)
    v.acts_list.selected_item = v.acts_list[1]
    refresh_gui()
    shouldbe = v.acts_holder.page_num(v.action_views['target'].widget)
    assert shouldbe == v.acts_holder.get_current_page()


def test_main_view_reorder_targets(b):
    v = PuilderView()
    v.set_build(b)
    refresh_gui()
    choosen = v.acts_list[0]
    print list(v.acts_list)

    v.acts_list.selected_item = choosen
    v.act_down_act.activate()
    v.acts_list.move_item_down(choosen)
    refresh_gui()
    print list(v.acts_list)

    assert v.acts_list[0] is not choosen
    assert v.acts_list[1] is choosen
    assert v.acts_list.selected_item is choosen

    v.act_up_act.activate()
    refresh_gui()
    print list(v.acts_list)

    assert v.acts_list[0] is choosen
    assert v.acts_list[1] is not choosen
    assert v.acts_list.selected_item is choosen



