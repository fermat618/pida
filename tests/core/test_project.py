from pida.core.projects import Project, DATA_DIR
import os
from unittest import TestCase
from tempfile import mkdtemp


main = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_create():
    p = Project(main)


class ProjectTest(TestCase):

    def setUp(self):
        if not hasattr(self, "ppath"):
            self.ppath = mkdtemp('pidatest')
            Project.create_blank_project_file('test', self.ppath)
            self.project = Project(self.ppath)

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
        
