"""
    Classes for Command based vcs's
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :license: BSD
"""

from subprocess import Popen, PIPE, STDOUT
import os.path 

#TODO: more reviews

from bases import VCSBase, DVCSMixin
from file import StatedPath as Path

def relative_to(base_path):
    """
    will turn absolute paths to paths relative to the base_path

    .. warning:
        will only work on paths below the base_path
        other paths will be unchanged
    """
    base_path = os.path.normpath(base_path)
    l = len(base_path)
    def process_path(path):

        if path.startswith(base_path):
            return "." + path[l:]
        else:
            return path
    return process_path


class CommandBased(VCSBase):
    """
    Base class for all command based rcs's
    """
    #TODO: set up the missing actions

    def __init__(self, versioned_path):
        self.path = os.path.normpath( os.path.abspath(versioned_path) )
        self.base_path = self.find_basepath(self.path)
        if self.base_path is None:
            raise ValueError(
                    'VC Basepath for vc class %r'
                    'not found above %s'%(
                        self.__class__.__name__, 
                        self.path)
                    )

    @classmethod
    def find_basepath(cls, act_path):
        detected_path = None
        detected_sd = None
        op = None
        while act_path != op:
            if os.path.exists( os.path.join(act_path, cls.detect_subdir)):
                detected_path = act_path
                # continue cause some vcs's 
                # got the subdir in every path
            op = act_path
            act_path = os.path.dirname(act_path)
        return detected_path

    def process_paths(self, paths):
        """
        process paths for vcs's usefull for "relpath-bitches"
        """
        return paths

    def execute_command(self, args, result_type=str, **kw):
        if not args:
            raise ValueError('need a valid command')
        ret = Popen(
                [self.cmd] + args,
                stdout=PIPE,
                stderr=STDOUT,
                cwd=self.base_path,
                close_fds=True)
        if result_type is str:
            return ret.communicate()[0]
        elif result_type is iter:
            return iter(ret.stdout)
        elif result_type is file:
            return ret.stdout

    def get_commit_args(self, message, paths=(), **kw):
        """
        creates a argument list for commiting

        :param message: the commit message
        :param paths: the paths to commit
        """
        return ['commit','-m', message] + self.process_paths(paths)

    def get_diff_args(self, paths=(), **kw):
        return ['diff'] + self.process_paths(paths)

    def get_update_args(self, revision=None, **kw):
        if revision:
            return ['update', '-r', revision]
        else:
            return ['update']

    def get_add_args(self, paths=(), recursive=False, **kw):
        return ['add'] + self.process_paths(paths)

    def get_remove_args(self, paths=(), recursive=False, execute=False, **kw):
        return ['remove'] +  self.process_paths(paths)

    def get_revert_args(self, paths=(), recursive=False, **kw):
        return ['revert'] + self.process_paths(paths)

    def get_status_args(self,**kw):
        return ['status']

    def get_list_args(self, **kw):
        raise NotImplementedError("%s doesnt implement list"%self.__class__.__name__)

    def commit(self, **kw):
        args = self.get_commit_args(**kw)
        return self.execute_command(args, **kw)

    def diff(self, **kw):
        args = self.get_diff_args(**kw)
        return self.execute_command(args, **kw)

    def update(self, **kw):
        args = self.get_update_args(**kw)
        return self.execute_command(args, **kw)

    def status(self, **kw):
        args = self.get_status_args(**kw)
        return self.execute_command(args, **kw)

    def add(self, **kw):
        args = self.get_add_args(**kw)
        return self.execute_command(args, **kw)

    def remove(self, **kw):
        args = self.get_remove_args(**kw)
        return self.execute_command(args, **kw)

    def revert(self, **kw):
        args = self.get_revert_args(**kw)
        return self.execute_command(args, **kw)

    def list_impl(self, **kw):
        """
        the default implementation is only cappable of 
        recursive operation on the complete workdir

        rcs-specific implementations might support 
        non-recursive and path-specific listing
        """
        args = self.get_list_args(**kw)
        return self.execute_command(args, result_type=iter, **kw)

    def cache_impl(self, recursive, **kw):
        """
        only runs caching if it knows, how
        """
        args = self.get_cache_args(**kw)
        if args:
            return self.execute_command(args, result_type=iter, **kw)
        else:
            return []

    def get_cache_args(self, **kw):
        return None


class DCommandBased(CommandBased,DVCSMixin):
    """
    base class for all distributed command based rcs's
    """
    def sync(self, **kw):
        args = self.get_sync_args(**kw)
        return self._execute_command(args, **kw)

    def pull(self, **kw):
        args = self.get_pull_args(**kw)
        return self._execute_command(args, **kw)

    def push(self, **kw):
        args = self.get_push_args(**kw)
        return self._execute_command(args, **kw)



class Bazaar(DCommandBased):
    """
    .. warning:
        badly broken
    """
    #TODO: fix caching
    cmd = "bzr"

    detect_subdir = ".bzr"

    def process_paths(self, paths):
        return map(relative_to(self.base_path), paths)

    def get_list_args(self, recursive=True, paths=(),**kw):
        ret = ["ls","-v"]
        if not recursive:
            ret.append("--non-recursive")
        return ret

    def get_cache_args(self, **kw):
        return ["st"]

    statemap  = {
            "unknown:": 'none',
            "added:": 'new',
            "unchanged:": 'normal',
            "removed:": 'removed',
            "ignored:": 'ignored',
            "modified:": 'modified',
            "conflicts:": 'conflict',
            "pending merges:": None,
            }

    def parse_cache_items(self, items):
        state = 'none'
        for item in items:
            item = item.rstrip()
            state = self.statemap.get(item.rstrip(), state)
            if item.startswith("  ") and state:
                yield item.strip(), state

    def parse_list_items(self, items, cache):
        for item in items:
            if item.startswith('I'):
                yield Path(item[1:].strip(), 'ignored', self.base_path)
            else:
                fn = item[1:].strip()
                yield Path(
                        fn,
                        cache.get(fn, 'normal'),
                        self.base_path)


class SubVersion(CommandBased):
    cmd = "svn"
    detect_subdir = ".svn"

    def get_list_args(self, recursive=True, paths=(), **kw):
        #TODO: figure a good way to deal with changes in external
        # (maybe use the svn python api to do that)
        ret = ["st", "--no-ignore", "--ignore-externals", "--verbose"]
        if not recursive:
            ret.append("--non-recursive")
        return ret + paths

    state_map = {
            "?": 'none',
            "A": 'new',
            " ": 'normal',
            "!": 'missing',
            "I": 'ignored',
            "M": 'modified',
            "D": 'removed',
            "C": 'conflict',
            'X': 'external',
            'R': 'modified',
            '~': 'external',
            }

    def parse_list_item(self, item, cache):
        state = item[0]
        file = item.split()[-1]
        #TODO: handle paths with whitespace if ppl fall in that one
        return Path(file, self.state_map[state], self.base_path)


class Mercurial(DCommandBased):
    cmd = "hg"
    detect_subdir = ".hg"

    def get_list_args(self, **kw):
        return ["status", "-A"]

    state_map = {
            "?": 'none',
            "A": 'new',
            " ": 'normal',
            "C": 'normal', #Clean
            "!": 'missing',
            "I": 'ignored',
            "M": 'modified',
            "R": 'removed',
            }

    def parse_list_item(self, item, cache):
        state = self.state_map[item[0]]
        file = item[2:].strip()
        return Path(file, state, self.base_path)


class Darcs(DCommandBased):
    #TODO: ensure this really works in most cases

    cmd = 'darcs'
    detect_subdir = '_darcs'

    def get_list_args(self, **kw):
        return ['whatsnew', '--boring', '--summary']

    state_map = {
        "a": 'none',
        "A": 'new',
        "M": 'modified',
        "C": 'conflict',
        "R": 'removed'
    }

    def parse_list_item(self, item, cache):
        if item.startswith('What') or item.startswith('No') or not item.strip():
            return None
        elements = item.split(None, 2)[:2] #TODO: handle filenames with spaces
        state = self.state_map[elements[0]]
        file = os.path.normpath(elements[1])
        return Path(file, state, self.base_path)


class Git(CommandBased):
    """
    experimental
    copyed processing from http://www.geekfire.com/~alex/pida-git.py by alex
    """
    cmd = 'git'
    detect_subdir = '.git'

    statemap = {
        None: 'normal',
        "new file": 'new',
        "": 'normal',
        "modified": 'modified',
        "unmerged": 'conflict',
        "deleted": 'removed'
        }

    def process_paths(self, paths):
        return map(relative_to(self.base_path), paths)

    def get_commit_args(self, message, paths=()):
        if paths:
            # commit only for the supplied paths
            return ['commit', '-m', message, '--'] + self.process_paths(paths)
        else:
            # commit all found changes
            # this also commits deletes ?!
            return ['commit', '-a', '-m', message]

    def get_revert_args(self, paths=(), recursive=False, **kw):
        return ['checkout'] + self.process_paths(paths)

    def get_list_args(self, **kw):
        return ['ls-tree', '-r', 'HEAD']

    def get_cache_args(self, **kw):
        return ['status']

    def parse_list_items(self, items, cache):
        for item in items:
            item = item.split()[-1]
            path = Path(item, cache.get(item, 'normal'), self.base_path)
            yield path

    def parse_cache_items(self, items):
        #TODO: fix the mess
        for a in items:
            if not a:continue
            ev, date, options, tag = [""]*4
            if a.startswith('#\t'):
                a = a.strip("#\t")
            if a.startswith('('):
                continue # ignore some odd lines
            state_and_name = a.split(':')
            if len(state_and_name) < 2:
                yield state_and_name[0].strip(), 'normal'
            else:
                yield state_and_name[1].strip(), self.statemap.get(state_and_name[0].strip())


