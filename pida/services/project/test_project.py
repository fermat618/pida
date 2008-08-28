# -*- coding: utf-8 -*- 
"""
    :copyright: 2008 by Ronny Pfannschmidt
    :license: GPL3 or later
"""

import os
from pida.core.projects import Project
from .project import ProjectService
from pida.utils.testing.mock import Mock

def test_loaded_event():
    boss = Mock()
    
    project_service = ProjectService(boss)
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
    got = project_service._load_project('.') #XXX: hack
    assert got is caught[0]


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
