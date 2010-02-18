# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import os, sys, traceback
from subprocess import Popen, PIPE, STDOUT
from StringIO import StringIO
from optparse import OptionParser
try:
    import select
except ImportError:
    select = None


from pida.core.projects import Project

from pida.utils.puilder.model import Build



def _info(*msg):
    """Write an informative message to stderr"""
    sys.stderr.write('\n'.join(msg) + '\n')

STDOUT = 1
STDERR = 2

class ActionBuildError(RuntimeError):
    pass

class Data(str):
    def __new__(cls, s, fd=STDOUT):
        rv = super(Data, cls).__new__(cls, s)
        rv.fd = fd
        return rv

    def __repr__(self):
        return '<Data %s %s>' %(self.fd, str.__repr__(self))

class OutputBuffer(StringIO):
    """
    Works like a StringIO, but saves Data objects on write
    Each data knows from which fd it came from and so, the output is 
    easier to process.
    """
    def write(self, s, fd=STDOUT):
        line = Data(s)
        line.fd = fd
        StringIO.write(self, line)

    def __repr__(self):
        return "<OutputBuffer %r>"%self.getvalue()

    def dump(self):
        return ''.join([repr(x) for x in self.buflist])


def proc_communicate(proc, stdin=None, stdout=None, stderr=None):
    """
    Run the given process, piping input/output/errors to the given
    file-like objects (which need not be actual file objects, unlike
    the arguments passed to Popen).  Wait for process to terminate.

    Note: this is taken from the posix version of
    subprocess.Popen.communicate, but made more general through the
    use of file-like objects.
    """
    read_set = []
    write_set = []
    input_buffer = ''
    trans_nl = proc.universal_newlines and hasattr(open, 'newlines')

    if proc.stdin:
        # Flush stdio buffer.  This might block, if the user has
        # been writing to .stdin in an uncontrolled fashion.
        proc.stdin.flush()
        if input:
            write_set.append(proc.stdin)
        else:
            proc.stdin.close()
    else:
        assert stdin is None
    if proc.stdout:
        read_set.append(proc.stdout)
    else:
        assert stdout is None
    if proc.stderr:
        read_set.append(proc.stderr)
    else:
        assert stderr is None

    while read_set or write_set:
        rlist, wlist, xlist = select.select(read_set, write_set, [])

        if proc.stdin in wlist:
            # When select has indicated that the file is writable,
            # we can write up to PIPE_BUF bytes without risk
            # blocking.  POSIX defines PIPE_BUF >= 512
            next, input_buffer = input_buffer, ''
            next_len = 512-len(next)
            if next_len:
                next += stdin.read(next_len)
            if not next:
                proc.stdin.close()
                write_set.remove(proc.stdin)
            else:
                bytes_written = os.write(proc.stdin.fileno(), next)
                if bytes_written < len(next):
                    input_buffer = next[bytes_written:]

        if proc.stdout in rlist:
            data = os.read(proc.stdout.fileno(), 1024)
            if data == "":
                proc.stdout.close()
                read_set.remove(proc.stdout)
            if trans_nl:
                data = proc._translate_newlines(data)
            sys.stdout.write(data)
            sys.stdout.flush()
            stdout.write(data, fd=STDOUT)

        if proc.stderr in rlist:
            data = os.read(proc.stderr.fileno(), 1024)
            if data == "":
                proc.stderr.close()
                read_set.remove(proc.stderr)
            if trans_nl:
                data = proc._translate_newlines(data)
            sys.stderr.write(data)
            sys.stderr.flush()
            stderr.write(data, fd=STDERR)

    try:
        proc.wait()
    except OSError, e:
        if e.errno != 10:
            raise



def _execute_external(cmd, cwd):

    buffer = OutputBuffer()

    if select:
        proc = Popen(cmd, bufsize=0, shell=True, cwd=cwd, 
                  stdout=PIPE, stderr=PIPE)

        proc_communicate(
            proc,
            stdout=buffer,
            stderr=buffer)
        #print buffer.dump()
        #print buffer.getvalue()

    else:
        #FIXME: dear win32 hacker, this should be fixed somehow :-)
        # as a workaround, output filters are disabled
        proc = Popen(cmd, bufsize=0, shell=True, cwd=cwd, 
                      stdout=None, stderr=None)
        stdout, stderr = proc.communicate()

    return buffer, proc.returncode


def execute_shell_action(project, build, action):
    """Execute a shell action"""
    cwd = action.options.get('cwd', project)
    cmd = action.value
    output, returncode = _execute_external(cmd, cwd)
    return output, not returncode



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
    try:
        _execute_python(project, build, action.value)
        success = True
    except Exception, e:
        traceback.print_exc(file=s)
        success = False
    s.seek(0)
    data = s.read()
    sys.stdout = oldout
    sys.stdout.write(data)
    return data, success

def execute_external_action(project, build, action):
    """Execute an external action"""
    cmd = '%s %s %s' % (
        action.options.get('system', 'make'),
        action.options.get('build_args', ''),
        action.value,
    )
    cwd = action.options.get('cwd', project)
    data, returncode = _execute_external(cmd, cwd)
    return data, not returncode


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
        raise KeyError(name)


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
            result, success = execute_action(build, action, project_directory)
            if success:
                yield result
            elif action.options['ignore_fail']:
                _info('--', 'Ignoring error in action', '--')
                yield result
            else:
                raise ActionBuildError()


def execute_target(project_file, target_name, project_directory=None):
    build = Build.loadf(project_file)
    return execute_build(build, target_name, project_directory)


def execute_project(project_directory, target_name):
    _info('Working dir: %s' % project_directory)
    project_file = Project.data_dir_path(project_directory, 'project.json')
    _info('Build file path: %s' % project_file, '--')
    sys.path.insert(0, project_directory)
    try:
        for action in execute_target(project_file, target_name, project_directory):
            pass
        _info('--', 'Build completed.')
    except ActionBuildError:
        _info('--', 'Error: Build failed.')


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



