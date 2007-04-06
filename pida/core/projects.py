"""Project features for PIDA"""

import os
from weakref import proxy

from configobj import ConfigObj


class ProjectControllerMananger(object):

    def __init__(self, boss=None):
        self.boss = boss
        self._controller_types = {}

    def register_controller(self, controller):
        # XXX: fix to raise error if already exists
        self._controller_types[controller.name] = controller

    def get_controller_type(self, name):
        return self._controller_types.get(name, None)

    def create_project(self, project_file):
        project = Project(self, project_file)
        return project


class Project(object):

    def __init__(self, manager, project_file):
        self.manager = manager
        self.boss = self.manager.boss
        self.project_file = project_file
        self.source_directory = os.path.dirname(self.project_file)
        self._create_options()
        self._create_controllers()
        self._register_actions()

    def _create_controllers(self):
        self.controllers = []
        for section in self.options.sections:
            controller_name = self.options.get(section).get('controller', None)
            if controller_name is not None:
                controller_type = self.manager.get_controller_type(controller_name)
                if controller_type is not None:
                    self.controllers.append(controller_type(self, section))
                else:
                    print 'no controller type for %s' % controller_name
            else:
                print 'no controller defined for %s' % section

    def _create_options(self):
        self.options = ConfigObj(self.project_file)

    def _register_actions(self):
        self.actions = {}
        self.action_kinds = {}
        for controller in self.controllers:
            for name, action in controller.actions.items():
                self.actions[name] = action
            for name, actions in controller.action_kinds.items():
                self.action_kinds.setdefault(name, []).extend(actions)

    def get_actions(self):
        return self.actions.values()

    def get_action(self, name):
        return self.actions[name]

    def get_actions_of_kind(self, kind):
        return self.action_kinds[kind]

    def set_option(self, section, name, value):
        self.options[section][name] = value
        self.options.write()

def project_action(kind):
    def project_action_decorator(f):
        f.__kind__ = kind
        f.__action__ = True
        return f
    return project_action_decorator


class ExecutionActionType(object):
    """A controller for execution"""

class BuildActionType(object):
    """A controller action for building"""

class TestActionType(object):
    """A controller action for testing"""

class ProjectController(object):

    name = ''

    glade_resource = None

    def __init__(self, project, config_section):
        self.project = proxy(project)
        self.boss = self.project.boss
        self.config_section = config_section
        self._register_actions()

    def _register_actions(self):
        self.actions = {}
        self.action_kinds = {}
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, '__action__'):
                self.actions[name] = attr
                self.action_kinds.setdefault(attr.__kind__, []).append(attr)

    def get_options(self):
        return self.project.options.get(self.config_section)

    def get_option(self, name):
        return self.get_options().get(name, None)

    def get_project_option(self, name):
        return self.project.options.get(name, None)

    def get_actions(self):
        return self.actions.values()

    def get_action(self, name):
        return self.actions[name]

    def get_actions_of_kind(self, kind):
        return self.action_kinds[kind]

    def execute_commandargs(self, args, env, cwd):
        print 'execute', args, env, cwd

    def execute_commandline(self, command, env, cwd):
        pass


# an example controller

class GenericExecutionController(ProjectController):

    name = 'GENERIC_EXECUTION'

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandline(
            self.get_option('command_line'),
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

class PythonController(ProjectController):

    name = 'PYTHON_CONTROLLER'

    @project_action(kind=BuildActionType)
    def build(self):
        self.execute_commandargs(
            [self.get_python_executable(), 'setup.py', 'build'],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    @project_action(kind=TestActionType)
    def test(self):
        self.execute_commandargs(
            [self.get_option('test_command')],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    @project_action(kind=ExecutionActionType)
    def execute(self):
        self.execute_commandargs(
            [self.get_python_executable(), self.get_option('execute_file')],
            self.get_option('env'),
            self.get_option('cwd') or self.project.source_directory,
        )

    def get_python_executable(self):
        return self.get_option('python_executable') or 'python'



