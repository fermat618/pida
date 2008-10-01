from pida.core.projects import Project, DATA_DIR
import os
from unittest import TestCase
from tempfile import mkdtemp


main = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_create():
    p = Project(main)
    
class ProjectTest(TestCase):

    def test_meta_dir(self):
        ppath = mkdtemp('pidatest')
        Project.create_blank_project_file('test', ppath)
        p = Project(ppath)
        m1 = p.get_meta_dir()
        self.assertEqual(m1, os.path.join(ppath, DATA_DIR))
        self.assertEqual(os.path.exists(m1), True)
        m2 = p.get_meta_dir('plug1')
        self.assertEqual(m2, os.path.join(ppath, DATA_DIR, 'plug1'))
        self.assertEqual(os.path.exists(m2), True)
        

