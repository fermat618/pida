from pida.utils import json
import pytest
import py

def pytest_funcarg__tmpfile(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    return tmpdir/'file.json'

def test_dump(tmpfile):
    json.dump({'name':1}, tmpfile)
    assert tmpfile.read() == '{\n  "name": 1\n}'

def test_load_missing(tmpfile):
    with pytest.raises(py.error.ENOENT):
        json.load(tmpfile)

def test_load_invalid(tmpfile):
    tmpfile.write('{ invalid')

    with py.test.raises(ValueError):
        json.load(tmpfile)

def test_load_fallback(tmpfile):
    ret = json.load(tmpfile, fallback=1)
    assert ret==1

def test_load_valid(tmpfile):

    test_dump(tmpfile)
    assert json.load(tmpfile) == {'name': 1}
