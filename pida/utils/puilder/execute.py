#! /usr/bin/env python

from subprocess import Popen, call

from pida.core.projects import Project

from pida.utils.puilder.model import Build



def execute_shell_action(project, build, action):
    print 'Shell Action: %s' % action.value
    print '--'
    p = Popen(action.value, shell=True, cwd=project)
    p.wait()
    print '--'

def _execute_python(source_directory, build, value):
    import sys
    print sys.path
    import os
    print os.environ['PYTHONPATH']
    code = compile(value + '\n', '<string>', 'exec')
    elocals = {
        'source_directory': source_directory,
        'build': build,
    }
    exec code in elocals, globals()

def execute_python_action(project, build, action):
    print 'Python action'
    print '--'
    _execute_python(project, build, action.value)
    print '--'

executors = {
    'shell': execute_shell_action,
    'python': execute_python_action,
}

def _load_build(path):
    f = open(path, 'r')
    json = f.read()
    b = Build.loads(json)
    f.close()
    return b

def execute_action(project, build, action):
    executors[action.type](project, build, action)

def execute_target(project, path, target):
    print 'Target: %s' % target
    print 'Working dir : %s' % project
    print 'Build file path: %s' % path
    print '--'
    b = _load_build(path)
    targets = [t for t in b.targets if t.name == target]
    if targets:
        t = targets[0]
        print 'Actions: %s' % len(t.actions)
        print '--'
        for act in t.actions:
            execute_action(project, b, act)
    else:
        raise RuntimeError('Target not found')

def execute(project, target):
    execute_target(project,
        Project.data_dir_path(project, 'project.json'),
        target)

if __name__ == '__main__':
    execute_target('.', 'test', 'testi')



