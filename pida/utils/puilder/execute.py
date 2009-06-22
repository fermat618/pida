# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import os, sys
from subprocess import Popen, PIPE, STDOUT
from StringIO import StringIO
from optparse import OptionParser

from pida.core.projects import Project

from pida.utils.puilder.model import Build



def _info(*msg):
    """Write an informative message to stderr"""
    sys.stderr.write('\n'.join(msg) + '\n')


def execute_shell_action(project, build, action):
    """Execute a shell action"""
    cwd = action.options.get('cwd', project)
    p = Popen(action.value, shell=True, cwd=cwd, stdout=PIPE, stderr=STDOUT)
    buffer = []
    for line in p.stdout:
        buffer.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()
    p.wait()
    return ''.join(buffer)


def _execute_python(source_directory, build, value):
    code = compile(value + '\n', '<string>', 'exec')
    elocals = {
        'source_directory': source_directory,
        'build': build,
    }
    exec code in elocals, globals()

def execute_python_action(project, build, action):
    """Execute a python action"""
    s = StringIO()
    oldout = sys.stdout
    sys.stdout = s
    _execute_python(project, build, action.value)
    s.seek(0)
    data = s.read()
    sys.stdout = oldout
    sys.stdout.write(data)
    return data

def execute_external_action(project, build, action):
    """Execute an external action"""
    cmd = '%s %s %s' % (
        action.options.get('system', 'make'),
        action.options.get('build_args', ''),
        action.value,
    )
    p = Popen(cmd, shell=True, close_fds=True, stdout=PIPE, stderr=STDOUT)
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
    """A node in the execution tree"""

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
    sys.path.insert(0, project_directory)
    for action in execute_target(project_file, target_name, project_directory):
        pass


execute = execute_project


def list_project_targets(project_directory):
    _info('Listing targets', '--')
    _info('Working dir: %s' % project_directory)
    project_file = Project.data_dir_path(project_directory, 'project.json')
    _info('Build file path: %s' % project_file, '--')
    build = Build.loadf(project_file)
    _info(*[t.name for t in build.targets])



def main():
    parser = OptionParser(usage='%prog [options] [target_name]')

    parser.add_option('-l', '--list', dest='do_list', action='store_true',
                      help='list targets')
    opts, args = parser.parse_args(sys.argv)

    project_directory = os.getcwd()

    if opts.do_list or len(args) < 2:
        list_project_targets(project_directory)
        _info('--', 'Run with target name to execute.')
        return 0

    target_name = args[1]

    execute_project(project_directory, target_name)


if __name__ == '__main__':
    sys.exit(main())



