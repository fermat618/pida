from pida.ui.widgets import ProxyStringList

def pytest_funcarg__pl(request):
    return ProxyStringList()

def test_proxy_stringlist_create():
    pl = ProxyStringList()
    assert not pl.view.get_headers_visible()


def test_sl_set_value(pl):
    pl.value = ['a', 'b']

    assert pl.value == ['a', 'b']


def test_sl_add_button(pl):
    assert len(pl.value) == 0
    pl.add_button.clicked()
    assert pl.value == ['New Item']

def test_sl_add_selects(pl):
    pl.add_button.clicked()
    text = pl.value_entry.get_text()
    assert text == 'New Item'
    assert pl.value_entry.props.editable

def test_pl_remove_desensible(pl):
    pl.add_button.clicked()
    pl.rem_button.clicked()
    assert pl.value == []
    assert not pl.value_entry.props.sensitive
    assert not pl.value_entry.get_text()
    pl.add_button.clicked()

    assert pl.value_entry.props.sensitive



def test_pl_edit(pl):
    pl.add_button.clicked()
    pl.value_entry.set_text('test')
    assert pl.value == ['test']
