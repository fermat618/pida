from pida.core.projects import Project, DATA_DIR, RESULT
import os

main = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_create():
    Project(main)


def mkfile(path):
    fp = open(path, "w")
    fp.close()

def rmdir(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)

def make_project_files(tmpdir):
    dirs = [
            'src',
            'lib',
            '.SVN',
            'src/.SVN',
            'src/CVS',
            'src/test2',
            'lib/bla',
            'lib/CVS'
            ]
    for dir in dirs:
        tmpdir.ensure(dir, dir=True)

    files = [
        'src/source.c',
        'src/source2.c',
        'src/source2.h',
        'src/skript.sh',
        'src/Makefile',
        'lib/Makefile',
        'lib/readme',
        'lib/bla/readme',
        'LICENSE',
        '.hiddenfile',
    ]
    for file in files:
        tmpdir.ensure(file)

def pytest_funcarg__project(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    Project.create_blank_project_file('test', str(tmpdir))
    return Project(str(tmpdir))

def test_meta_dir(project, tmpdir):
    m1 = project.get_meta_dir()
    assert m1 == tmpdir.join(DATA_DIR)
    assert os.path.exists(m1)
    m2 = project.get_meta_dir('plug1')
    assert m2 == tmpdir.join(DATA_DIR, 'plug1')
    assert os.path.exists(m2)

def test_relpath(project, tmpdir):
    check = str(tmpdir.join('something', 'else.py'))
    relative = project.get_relative_path_for(check)
    assert relative == ["something", "else.py"]

    assert project.get_relative_path_for(project.source_directory) == []


def test_cache(project, tmpdir):
    project.load_cache()
    #XXX: added cause of fucked cache
    project.index('', recrusive=True)

    c = project._cache
    #the empty cache should contain the root elements and the metadata
    assert len(c['dirs']) == 2
    assert len(c['paths']) == 3
    assert len(c['dirnames']) == 2
    assert len(c['files']) == 1
    assert len(c['filenames']) == 1

    tmpdir.ensure('src', dir=True)
    tmpdir.ensure('lib', dir=True)

    project.index(recrusive=True)
    assert sorted(c['dirnames']) == ['', '.pida-metadata', 'lib', 'src']
    assert sorted(c['dirs']) == ['', '.pida-metadata', 'lib', 'src']

    tmpdir.ensure("src", "test", dir=True)
    tmpdir.ensure("outside", dir=True)
    project.index("src", recrusive=True)

    print sorted(c['dirs'])
    assert sorted(c['dirnames']) == ['', '.pida-metadata', 'lib', 'src', 'test']
    assert sorted(c['dirs']) == ['', '.pida-metadata', 'lib', 'src', 'src/test']

    assert 'outside' not in c['dirs']
    assert 'outside' not in c['dirnames']

    #generate dummy data
    make_project_files(tmpdir)
    project.index("", recrusive=True)

    # test doctypes
    assert c['files']['LICENSE'].doctype is None
    assert c['files']['src/source2.c'].doctype == 'C'
    assert c['files']['src/skript.sh'].doctype == 'Bash'

    assert len(c['filenames']['readme']) == 2
    assert len(c['filenames']['Makefile']) == 2
    assert len(c['dirnames']['src']) == 1
    assert len(c['dirnames']['CVS']) == 2

    # start removing files
    tmpdir.join('lib', 'bla').remove(rec=True)
    assert not tmpdir.join('lib', 'bla').check()
    project.index('lib', recrusive=True)

    assert 'bla' not in c['dirnames']
    assert 'bla' not in c['paths']
    assert len(c['filenames']['readme']) == 1
    assert len(c['filenames']['Makefile']) == 2
    assert len(c['dirnames']['src']) == 1
    assert len(c['dirnames']['CVS']) == 2

    dirs = [
        '.SVN',
        'src/.SVN',
        'src/CVS',
        'src/test2',
        'lib/CVS',
    ]

    files = [
        'src/source.c',
        'src/source2.c',
        'src/source2.h',
        'src/skript.sh',
        'src/Makefile',
        'lib/Makefile',
        'lib/readme',
        'LICENSE',
        '.hiddenfile',
        ]
    print sorted(c['dirs'])
    assert set(files).issubset(c['files'])
    assert set(dirs).issubset(c['dirs'])

    assert set(files).issubset(c['paths'])
    assert set(dirs).issubset(c['paths'])

    # save the state and reload
    project.save_cache()
    assert project.load_cache()
    c = project._cache  # loadin sets the cache

    assert set(files).issubset(c['files'])
    assert set(dirs).issubset(c['dirs'])

    assert set(files).issubset(c['paths'])
    assert set(dirs).issubset(c['paths'])

    # test for equality of instances
    assert c['paths']['src/source2.h'] == c['filenames']["source2.h"][0]

    # add new file
    tmpdir.ensure('src/blubb')
    tmpdir.ensure('src/noho', dir=True)
    project.index('src/blubb')
    project.index('src/noho')
    assert len(c['filenames']['blubb']) == 1
    assert c['files']['src/blubb'].relpath == 'src/blubb'

    assert len(c['dirnames']['noho']) == 1
    assert c['dirs']['src/noho'].relpath == 'src/noho'


def test_query(project, tmpdir):
    make_project_files(tmpdir)

    project.index(recrusive=True)
    def query(*k, **kw):
        return [x.relpath for x in project.query_basename(*k, **kw)]

    assert query('source.c') == ['src/source.c']
    rel = query('source.c')[0]
    assert rel == project._cache['filenames']['source.c'][0].relpath

    # non existing through wrong case
    assert query('source.c2') == []
    assert query('source.C') == []
    assert query('') == []

    assert query('source.c2', dirs=True) == []
    assert query('source.C', dirs=True) == []

    # test for directories
    assert query('lib') == []
    assert query('lib', dirs=True) == ['lib']
    assert query('liB', dirs=True) == []

    assert query('lib', dirs=True, glob=True) == ['lib']
    #globs
    assert len(query('l??', dirs=True, glob=True)) == 1
    assert len(query('source.*', glob=True)) == 1
    assert len(query('source2.?', glob=True)) == 2
    assert len(query('source*', glob=True)) == 3

    rv =  sorted(query(None))
    assert rv == ['.hiddenfile', '.pida-metadata/project.json',
                  'LICENSE', 'lib/Makefile', 'lib/bla/readme',
                  'lib/readme', 'src/Makefile', 'src/skript.sh',
                  'src/source.c', 'src/source2.c', 'src/source2.h']
    rv = sorted(query(None, dirs=True))
    assert rv == ['', '.SVN', '.hiddenfile', '.pida-metadata',
                  '.pida-metadata/project.json', 'LICENSE', 'lib',
                  'lib/CVS', 'lib/Makefile', 'lib/bla', 'lib/bla/readme',
                  'lib/readme', 'src', 'src/.SVN', 'src/CVS',
                  'src/Makefile', 'src/skript.sh', 'src/source.c',
                  'src/source2.c', 'src/source2.h', 'src/test2']

    # test query interface

    # test for a filetype
    def find_file(info):
        if info.doctype == "C":
            return RESULT.YES
        return RESULT.NO

    bases = [x.basename for x in project.query(find_file)]
    assert bases == ['source.c', 'source2.c', 'source2.h']

    # test subdir check
    def find_subdir(info):
        if info.basename == "lib":
            return RESULT.NO_NOCHILDS
        elif info.is_dir:
            return RESULT.YES

    bases = [x.relpath for x in project.query(find_subdir)]
    print bases

    assert bases == ['', '.SVN', '.pida-metadata', 'src', 'src/.SVN',
                     'src/CVS', 'src/test2']

    def testc(info):
        if info.basename == "lib":
            return RESULT.YES_NOCHILDS
        return RESULT.YES

    bases = [x.relpath for x in project.query(testc)]
    assert bases == ['', '.SVN', '.hiddenfile', '.pida-metadata',
                    '.pida-metadata/project.json', 'LICENSE', 'lib',
                    'src', 'src/.SVN', 'src/CVS', 'src/Makefile',
                    'src/skript.sh', 'src/source.c', 'src/source2.c',
                    'src/source2.h', 'src/test2',
                    ]

