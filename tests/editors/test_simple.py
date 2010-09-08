import py

@py.test.mark.xfail(reason='unimplemented', run=False)
def test_start(editor):
    assert editor.started
