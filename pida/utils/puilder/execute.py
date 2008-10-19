#! /usr/bin/env python
import sys
from subprocess import Popen, call

from pida.core.projects import Project

from pida.utils.puilder.model import Build



def execute_shell_action(project, build, action):
    p = Popen(action.value, shell=True, cwd=project)
    p.wait()

def _execute_python(source_directory, build, value):
    sys.path.insert(0, source_directory)
    code = compile(value + '\n', '<string>', 'exec')
    elocals = {
        'source_directory': source_directory,
        'build': build,
    }
    exec code in elocals, globals()

def execute_python_action(project, build, action):
    _execute_python(project, build, action.value)

def execute_external_action(project, build, action):
    cmd = '%s %s %s' % (
        action.options.get('system', 'make'),
        action.options.get('build_args', ''),
        action.value,
    )
    p = Popen(cmd, shell=True, close_fds=True)
    p.wait()


executors = {
    'shell': execute_shell_action,
    'python': execute_python_action,
    'external': execute_external_action,
}

def _load_build(path):
    f = open(path, 'r')
    json = f.read()
    b = Build.loads(json)
    f.close()
    return b

def execute_action(project, build, action):
    executors[action.type](project, build, action)

def indent_print(s, indent):
    for line in s.splitlines():
        print '%s%s' % ('   .' * indent, line)

def execute_target(project, path, target, indent=0):
    indent_print('Target: %s' % target, indent)
    b = _load_build(path)
    targets = [t for t in b.targets if t.name == target]
    if targets:
        t = targets[0]
        indent_print('Dependencies: %s' % len(t.dependencies), indent)
        for dep in t.dependencies:
            execute_target(project, path, dep.name, indent + 1)
        indent_print('Actions: %s' % len(t.actions), indent)
        for act in t.actions:
            indent_print('[ %s ]' % act.type, indent)
            indent_print(act.value, indent)
            print '-' * 10 + ' +++  Output +++'
            execute_action(project, b, act)
            print "-" * 10
    else:
        indent_print('Target missing: %s' % target, indent)

def execute(project, target):
    print 'Working dir: %s' % project
    print "=" * 10
    path = Project.data_dir_path(project, 'project.json')
    print 'Build file path: %s' % path
    print "=" * 10
    execute_target(project, path, target)

if __name__ == '__main__':
    execute_target('.', 'test', 'testi')



