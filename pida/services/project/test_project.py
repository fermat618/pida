# -*- coding: utf-8 -*- 
"""
    :copyright: 2008 by the Pida Project
    :license: GPL2 or later
"""

import os
from pida.core.projects import Project
from .project import ProjectService
from pida.utils.testing.mock import Mock
from pida.core.environment import library
library.add_global_resource('glade', 
                            os.path.join(os.path.dirname(__file__), 'glade'))

def test_loaded_event():
    boss = Mock()
    
    project_service = ProjectService(boss)
    project_service.started = False
    project_service.create_all()
    project_service.start()
    #XXX: mock mimicing the result of project_service.pre_start
    project_service._projects = []
    project_service.project_list = Mock()
    project_service.project_list.project_ol = Mock()


    caught = []

    project_service.events.subscribe('loaded', 
            lambda project:caught.append(project)
            )
    # 
    # HACK: we assum the pida dev path, so we have a project to load :)
    DEVPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                os.path.pardir, os.path.pardir, os.path.pardir)) 
    got = project_service._load_project(DEVPATH) #XXX: hack
    assert got is caught[0]

def test_load_of_missing_project(tmpdir, monkeypatch):
    #XXX: log entries
    boss = Mock()
    boss.return_value = [str(tmpdir.join('missing-dir'))]
    svc = ProjectService(boss)
    monkeypatch.setattr(svc, 'opt', boss)

    svc._read_options()


def test_load_project_just_path(tmpdir, monkeypatch):
    boss = Mock()
    boss.return_value = [str(tmpdir)]
    svc = ProjectService(boss)
    monkeypatch.setattr(svc, 'opt', boss)


    def mock_load_project(dirname):
        assert dirname == tmpdir
    monkeypatch.setattr(svc, '_load_project', mock_load_project)
    svc._read_options()


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
