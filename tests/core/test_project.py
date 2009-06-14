from pida.core.projects import Project, DATA_DIR, RESULT
import os
from unittest import TestCase
from tempfile import mkdtemp
from functools import partial


main = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_create():
    p = Project(main)


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

pf = lambda *x: os.path.sep.join(x)


class ProjectTest(TestCase):

    def setUp(self):
        self.ppath = mkdtemp('pidatest')
        Project.create_blank_project_file('test', self.ppath)
        self.project = Project(self.ppath)

    def tearDown(self):
        # clean up temp directory
        rmdir(self.ppath)

    def test_meta_dir(self):
        ppath = self.ppath
        p = Project(ppath)
        m1 = p.get_meta_dir()
        self.assertEqual(m1, os.path.join(ppath, DATA_DIR))
        self.assertEqual(os.path.exists(m1), True)
        m2 = p.get_meta_dir('plug1')
        self.assertEqual(m2, os.path.join(ppath, DATA_DIR, 'plug1'))
        self.assertEqual(os.path.exists(m2), True)
    
    def test_relpath(self):
        self.assertEqual(self.project.get_relative_path_for(
            os.path.join(self.ppath, "something", "else.py")),
            ["something", "else.py"]
            )
        filename = os.path.join(self.ppath, "module", "mod2.py")
        self.assertEqual(
            ".".join(self.project.get_relative_path_for(filename))[:-3],
            'module.mod2'
            )
        self.assertEqual(self.project.get_relative_path_for(
                                self.project.source_directory), 
                         [])

    def make_project_files(self):
        pp = partial(os.path.join, self.project.source_directory)

        os.mkdir(pp(".SVN"))
        os.mkdir(pp("src", ".SVN"))
        os.mkdir(pp("src", "CVS"))
        os.mkdir(pp("src", "test2"))
        os.mkdir(pp("lib", "bla"))
        os.mkdir(pp("lib", "CVS"))
        mkfile(pp("src", "source.c"))
        mkfile(pp("src", "source2.c"))
        mkfile(pp("src", "source2.h"))
        mkfile(pp("src", "skrip.sh"))
        mkfile(pp("src", "Makefile"))
        mkfile(pp("lib", "Makefile"))
        mkfile(pp("lib", "readme"))
        mkfile(pp("lib", "bla", "readme"))
        mkfile(pp("LICENSE"))
        mkfile(pp(".hiddenfile"))


    def test_cache(self):
        self.project.load_cache()
        #the empty cache should contain the root elements and the metadata
        self.assertEqual(len(self.project._cache['dirs']), 2)
        self.assertEqual(len(self.project._cache['paths']), 3)
        self.assertEqual(len(self.project._cache['dirnames']), 2)
        self.assertEqual(len(self.project._cache['files']), 1)
        self.assertEqual(len(self.project._cache['filenames']), 1)


        pp = partial(os.path.join, self.project.source_directory)

        os.mkdir(pp("src"))
        os.mkdir(pp("lib"))
        self.project.index("", recrusive=True)
        self.assertTrue(
            all([x in self.project._cache['dirnames'] for x in 
                ['src', 'lib', '.pida-metadata']]))
        self.assertTrue(
            all([x in self.project._cache['dirs'] for x in 
                ['src', 'lib', '.pida-metadata']]))

        os.mkdir(pp("src", "test"))
        os.mkdir(pp("outside"))
        self.project.index("src", recrusive=True)

        self.assertTrue(
            all([x in self.project._cache['dirnames'] for x in 
                ['src', 'lib', '.pida-metadata', 'test']]))
        self.assertTrue(
            all([x in self.project._cache['dirs'] for x in 
                ['src', 'lib', '.pida-metadata', 'src/test']]))

        self.assertTrue(not 'outside' in self.project._cache['dirs'])
        self.assertTrue(not 'outside' in self.project._cache['dirnames'])

        #generate dummy data
        self.make_project_files()

        self.project.index("", recrusive=True)

        # test doctypes
        self.assertEqual(self.project._cache['files']['LICENSE'].doctype,
                         None)
        self.assertEqual(self.project._cache['files'][
                                    pf('src', 'source2.c')].doctype,
                         'C')
        self.assertEqual(self.project._cache['files'][
                                    pf('src', 'skrip.sh')].doctype,
                         'Bash')

        self.assertEqual(len(self.project._cache['filenames']['readme']), 2)
        self.assertEqual(len(self.project._cache['filenames']['Makefile']), 2)
        self.assertEqual(len(self.project._cache['dirnames']['src']), 1)
        self.assertEqual(len(self.project._cache['dirnames']['CVS']), 2)


        # start removing files
        rmdir(pp('lib', 'bla'))
        self.assertTrue(not os.path.exists(pp('lib', 'bla')))
        self.project.index(pf('lib'), recrusive=True)

        self.assertTrue(not 'bla' in self.project._cache['dirnames'])
        self.assertTrue(not pf('bla') in self.project._cache['paths'])
        self.assertEqual(len(self.project._cache['filenames']['readme']), 1)
        self.assertEqual(len(self.project._cache['filenames']['Makefile']), 2)
        self.assertEqual(len(self.project._cache['dirnames']['src']), 1)
        self.assertEqual(len(self.project._cache['dirnames']['CVS']), 2)

        dirs = [
            pf(".SVN"),
            pf("src", ".SVN"),
            pf("src", "CVS"),
            pf("src", "test2"),
            pf("lib", "CVS")]

        files = [
            pf("src", "source.c"),
            pf("src", "source2.c"),
            pf("src", "source2.h"),
            pf("src", "skrip.sh"),
            pf("src", "Makefile"),
            pf("lib", "Makefile"),
            pf("lib", "readme"),
            pf("LICENSE"),
            pf(".hiddenfile")]

        self.assertEqual(
            all([x in self.project._cache['files'] for x in files]), True)
        self.assertEqual(
            all([x in self.project._cache['dirs'] for x in dirs]), True)
        self.assertEqual(
            all([x in self.project._cache['paths'] for x in files + dirs]),
            True)

        # save the state and reload
        self.project.save_cache()
        self.project.load_cache()

        self.assertEqual(
            all([x in self.project._cache['files'] for x in files]), True)
        self.assertEqual(
            all([x in self.project._cache['dirs'] for x in dirs]), True)
        self.assertEqual(
            all([x in self.project._cache['paths'] for x in files + dirs]),
            True)

        # test for equality of instances
        self.assertEqual(self.project._cache['paths'][pf("src", "source2.h")], 
                         self.project._cache['filenames']["source2.h"][0])

        # add new file
        mkfile(pp('src', 'blubb'))
        os.mkdir(pp('src', 'noho'))
        self.project.index_path(pp('src', 'blubb'))
        self.project.index_path(pp('src', 'noho'))
        self.assertEqual(len(self.project._cache['filenames']['blubb']), 1)
        self.assertEqual(self.project._cache['files'][pf('src', 'blubb')].relpath,
                            pf('src', 'blubb'))
        
        self.assertEqual(len(self.project._cache['dirnames']['noho']), 1)
        self.assertEqual(self.project._cache['dirs'][pf('src', 'noho')].relpath,
                            pf('src', 'noho'))
        

    def test_query(self):
        pp = partial(os.path.join, self.project.source_directory)

        os.mkdir(pp("src"))
        os.mkdir(pp("lib"))
        self.make_project_files()

        self.project.index(recrusive=True)

        self.assertEqual(len(list(self.project.query_basename('source.c'))), 1)
        self.assertEqual(list(self.project.query_basename('source.c'))[0], 
                         self.project._cache['filenames']['source.c'][0])

        # non existing through wrong case
        self.assertEqual(len(list(self.project.query_basename('source.c2'))), 0)
        self.assertEqual(len(list(self.project.query_basename('source.C'))), 0)
        self.assertEqual(len(list(self.project.query_basename(''))), 0)

        self.assertEqual(
            len(list(self.project.query_basename('source.c2', dirs=True))), 0)
        self.assertEqual(
            len(list(self.project.query_basename('source.C', dirs=True))), 0)

        # test for directories
        self.assertEqual(len(list(self.project.query_basename('lib'))), 0)
        self.assertEqual(
            len(list(self.project.query_basename('lib', dirs=True))), 1)
        self.assertEqual(
            len(list(self.project.query_basename('liB', dirs=True))), 0)

        self.assertEqual(
           len(list(self.project.query_basename('lib', dirs=True, glob=True))),
           1)
        #globs
        self.assertEqual(
           len(list(self.project.query_basename('l??', dirs=True, glob=True))),
           1)
        self.assertEqual(
            len(list(self.project.query_basename('source.*', glob=True))), 1)
        self.assertEqual(
            len(list(self.project.query_basename('source2.?', glob=True))), 2)
        self.assertEqual(
            len(list(self.project.query_basename('source*', glob=True))), 3)

        rv = [x.relpath for x in self.project.query_basename(None)]
        rv.sort()
        self.assertEqual(rv, 
                         ['.hiddenfile', '.pida-metadata/project.json', 
                          'LICENSE', 'lib/Makefile', 'lib/bla/readme', 
                          'lib/readme', 'src/Makefile', 'src/skrip.sh', 
                          'src/source.c', 'src/source2.c', 'src/source2.h'])


        rv = [x.relpath for x in self.project.query_basename(None, dirs=True)]
        rv.sort()
        self.assertEqual(rv,
                        ['', '.SVN', '.hiddenfile', '.pida-metadata', 
                        '.pida-metadata/project.json', 'LICENSE', 'lib', 
                        'lib/CVS', 'lib/Makefile', 'lib/bla', 'lib/bla/readme', 
                        'lib/readme', 'src', 'src/.SVN', 'src/CVS', 
                        'src/Makefile', 'src/skrip.sh', 'src/source.c', 
                        'src/source2.c', 'src/source2.h', 'src/test2'])

        # test query interface

        # test for a filetype
        def testc(info):
            if info.doctype == "C":
                return RESULT.YES
            return RESULT.NO

        self.assertEqual([x.basename for x in 
                          self.project.query(testc)],
                         ['source.c', 'source2.c', 'source2.h'])

        # test subdir check
        def testc(info):
            if info.basename == "lib":
                return RESULT.NO_NOCHILDS
            elif info.is_dir:
                return RESULT.YES

        self.assertEqual([x.relpath for x in 
                          self.project.query(testc)],
                         ['', '.SVN', '.pida-metadata', 'src', 'src/.SVN', 
                          'src/CVS', 'src/test2'])

        def testc(info):
            if info.basename == "lib":
                return RESULT.YES_NOCHILDS
            return RESULT.YES

        self.assertEqual([x.relpath for x in 
                          self.project.query(testc)],
                         ['', '.SVN', '.hiddenfile', '.pida-metadata', 
                          '.pida-metadata/project.json', 'LICENSE', 'lib', 
                          'src', 'src/.SVN', 'src/CVS', 'src/Makefile', 
                          'src/skrip.sh', 'src/source.c', 'src/source2.c', 
                          'src/source2.h', 'src/test2'])

