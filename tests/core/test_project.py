from pida.core.projects import Project
import os

main = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_create():
    p = Project(main)
