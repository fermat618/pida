from unittest import TestCase

import os
from tempfile import mkstemp

# the matching example config file
from pida.core.projects import ProjectControllerMananger, project_action, ProjectController

ExecutionActionType=None

PYCONF="""
name = My Project
[Python]
controller = PYTHON_CONTROLLER
execute_file = banana.py
source_package = src
test_command = nosetests
"""

class GenericExecutionController(ProjectController):

    name = 'GENERIC_EXECUTION'

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandline(
            self.get_option('command_line'),
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

EXCONF = """
name = My Project
[Execution]
controller = GENERIC_EXECUTION
command_line = ls -al
"""

class BasicTest(TestCase):

    def setUp(self):
        self._pcm = ProjectControllerMananger()
        self._pcm.register_controller(GenericExecutionController)
        f, self._path = mkstemp()
        os.write(f, EXCONF)
        os.close(f)
        self._pr = self._pcm.create_project(self._path)

    def test_register(self):
        self.assertEqual(len(self._pr.action_kinds[ExecutionActionType]), 1)

    def test_execute(self):
        self._pr.controllers[0].execute_commandline = self._execute
        self._pr.action_kinds[ExecutionActionType][0]()
        self.assertEqual(len(self.args), 3)

    def test_set_option(self):
        self._pr.controllers[0].execute_commandline = self._execute
        self._pr.action_kinds[ExecutionActionType][0]()
        self.assertEqual(self.args[0], 'ls -al')
        self._pr.set_option('Execution', 'command_line', 'ls')
        self._pr.action_kinds[ExecutionActionType][0]()
        self.assertEqual(self.args[0], 'ls')

    def _execute(self, *args):
        self.args = args

    def tearDown(self):
        os.remove(self._path)




