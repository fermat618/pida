#! /usr/bin/env python
import sys, StringIO
from subprocess import Popen, PIPE

from pida.core.projects import Project

from pida.utils.puilder.model import Build



def _info(*msg):
    sys.stderr.write('\n'.join(msg) + '\n')

def execute_shell_action(project, build, action):
    cwd = action.options.get('cwd', project)
    p = Popen(action.value, shell=True, cwd=cwd, stdout=PIPE)
    buffer = []
    for line in p.stdout:
        buffer.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()
    p.wait()
    return ''.join(buffer)


def _execute_python(source_directory, build, value):
    sys.path.insert(0, source_directory)
    code = compile(value + '\n', '<string>', 'exec')
    elocals = {
        'source_directory': source_directory,
        'build': build,
    }
    exec code in elocals, globals()

def execute_python_action(project, build, action):
    s = StringIO.StringIO()
    oldout = sys.stdout
    sys.stdout = s
    _execute_python(project, build, action.value)
    s.seek(0)
    data = s.read()
    sys.stdout = oldout
    sys.stdout.write(data)
    return data

def execute_external_action(project, build, action):
    cmd = '%s %s %s' % (
        action.options.get('system', 'make'),
        action.options.get('build_args', ''),
        action.value,
    )
    p = Popen(cmd, shell=True, close_fds=True, stdout=PIPE)
    p.wait()
    return p.stdout.read()


executors = {
    'shell': execute_shell_action,
    'python': execute_python_action,
    'external': execute_external_action,
}


def _get_target(build, name):
    targets = [t for t in build.targets if t.name == name]
    if targets:
        return targets[0]
    else:
        raise KeyError


class CircularAction(object):
    """
    Define a circular action that can't be executed.
    """
    def __init__(self, target):
        self.target = target


class ExecutionNode(object):

    def __init__(self, build, target, action, parent):
        self.build = build
        self.target = target
        self.action = action
        self.circular = False
        self.ancestors = set()
        if parent is not None:
            self.ancestors.add(parent)
            self.ancestors.update(parent.ancestors)

        if self.action is None:
            # this is a target node
            self._generate_children()
        elif self.action.type == 'target':
            # this is a target action
            self.target = _get_target(build, action.value)
            self.action = None
            self._generate_children()
        else:
            # Plain action
            self.children = []

        self.actions = list(self.get_actions())

    def _is_circular(self, target):
        for ancestor in self.ancestors:
            if ancestor.target is target and ancestor.action is None:
                return True

    def _generate_children(self):
        if self._is_circular(self.target):
            self.children = []
            self.circular = True
        else:
            self.children = [ExecutionNode(self.build, self.target, a, self)
                                for a in self.target.actions]

    def get_actions(self):
        if self.action:
            yield self.action
        elif self.circular:
            yield CircularAction(self.target)
        else:
            for child in self.children:
                for ex in child.get_actions():
                    yield ex


def generate_execution_graph(build, target_name):
    target = _get_target(build, target_name)
    root = ExecutionNode(build, target, None, None)
    return root



def execute_action(build, action, project_directory):
    return executors[action.type](project_directory, build, action)


def execute_build(build, target_name, project_directory=None):
    graph = generate_execution_graph(build, target_name)
    for action in graph.actions:
        if isinstance(action, CircularAction):
            _info('--', 'Warning: Circular action ignored: %s' % action.target.name, '--')
        else:
            _info('Executing: [%s]' % action.type, '--', action.value, '--')
            yield execute_action(build, action, project_directory)
            _info('--')


def execute_target(project_file, target_name, project_directory=None):
    build = Build.loadf(project_file)
    return execute_build(build, target_name, project_directory)


def execute_project(project_directory, target_name):
    _info('Working dir: %s' % project_directory)
    project_file = Project.data_dir_path(project_directory, 'project.json')
    _info('Build file path: %s' % project_file, '--')
    for action in execute_target(project_file, target_name, project_directory):
        pass


execute = execute_project


if __name__ == '__main__':
    execute_target('.', 'test', 'testi')



