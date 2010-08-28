from pida.utils.symbols import Symbols
from py.test import raises


def pytest_funcarg__table(request):
    return Symbols('test', 'ab')


def test_attrs(table):
    assert table.A == 'a'
    assert table.B == 'b'

def test_content(table):
    assert table['a'] == 0
    assert table['b'] == 1
    assert table[0] == 'a'
    assert table[1] == 'b'

def test_needs_lower():
    raises(ValueError, Symbols, 'name', ['Foo'])

def test_contains(table):
    assert 'a' in table
    assert 'A' in table

def test_order():
    t = Symbols('test', 'ba')
    l = ['c', 'a', 'b']
    l.sort(key=t.key)
    #XXX: None sorts before anything else
    assert l == ['b', 'a', 'c']

def test_not_iterable(table):
    with raises(TypeError):
        list(table)
