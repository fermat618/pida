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
        self.base_path = self.find_basepath()
    
    def find_basepath(self):
        act_path = self.path
        detected_path = None
        detected_sd = None
        op = None
        while act_path != op:
            if os.path.exists( os.path.join(act_path, self.detect_subdir)):
                detected_path = act_path
                # continue cause some vcs's 
                # got the subdir in every path
            op = act_path
            act_path = os.path.dirname(act_path)
                
        if not detected_path:
            raise ValueError(
                    'VC Basepath for vc class %r'
                    'not found above %s'%(
                        type(self), 
                        self.path)
                    )

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


class Monotone(DCommandBased):
    
    cmd = 'mtn'
    
    detect_subdir = '_MTN'
    
    statemap = {
        '   ': 'normal',   # unchanged
        '  P': 'modified', # patched (contents changed)
        '  U': 'none',     # unknown (exists on the filesystem but not tracked)
        '  I': 'ignored',  # ignored (exists on the filesystem but excluded by lua hook)
        '  M': 'missing',  # missing (exists in the manifest but not on the filesystem)

        ' A ': 'error',    # added (invalid, add should have associated patch)
        ' AP': 'new',      # added and patched
        ' AU': 'error',    # added but unknown (invalid)
        ' AI': 'error',    # added but ignored (seems invalid, but may be possible)
        ' AM': 'empty',    # added but missing from the filesystem

        ' R ': 'normal',   # rename target
        ' RP': 'modified', # rename target and patched
        ' RU': 'error',    # rename target but unknown (invalid)
        ' RI': 'error',    # rename target but ignored (seems invalid, but may be possible?)
        ' RM': 'missing',  # rename target but missing from the filesystem

        'D  ': 'removed',  # dropped
        'D P': 'error',    # dropped and patched (invalid)
        'D U': 'error',  # dropped and unknown (still exists on the filesystem)
        'D I': 'error',    # dropped and ignored (seems invalid, but may be possible?)
        'D M': 'error',    # dropped and missing (invalid)

        'DA ': 'error',    # dropped and added (invalid, add should have associated patch)
        'DAP': 'new',      # dropped and added and patched
        'DAU': 'error',    # dropped and added but unknown (invalid)
        'DAI': 'error',    # dropped and added but ignored (seems invalid, but may be possible?)
        'DAM': 'missing',  # dropped and added but missing from the filesystem

        'DR ': 'normal',   # dropped and rename target
        'DRP': 'modified', # dropped and rename target and patched
        'DRU': 'error',    # dropped and rename target but unknown (invalid)
        'DRI': 'error',    # dropped and rename target but ignored (invalid)
        'DRM': 'missing',  # dropped and rename target but missing from the filesystem

        'R  ': 'missing',  # rename source
        'R P': 'error',    # rename source and patched (invalid)
        'R U': 'removed',  # rename source and unknown (still exists on the filesystem)
        'R I': 'error',    # rename source and ignored (seems invalid, but may be possible?)
        'R M': 'error',    # rename source and missing (invalid)

        'RA ': 'error',    # rename source and added (invalid, add should have associated patch)
        'RAP': 'new',      # rename source and added and patched
        'RAU': 'error',    # rename source and added but unknown (invalid)
        'RAI': 'error',    # rename source and added but ignored (seems invalid, but may be possible?)
        'RAM': 'missing',  # rename source and added but missing from the filesystem

        'RR ': 'new',      # rename source and target
        'RRP': 'modified', # rename source and target and target patched
        'RRU': 'error',    # rename source and target and target unknown (invalid)
        'RRI': 'error',    # rename source and target and target ignored (seems invalid, but may be possible?)
        'RRM': 'missing',   # rename source and target and target missing
    }

    def process_paths(self, paths):
        return map(relative_to(self.base_path), paths)

    def get_remove_args(self, paths, **kw):
        return ["drop"] + self.process_paths(paths)

    def get_list_args(self, **kw):
        return ["automate", "inventory"]

    def parse_list_item(self, item):
        state = self.statemap.get(item[:3], "none")
        return Path(os.path.normpath(item[8:].rstrip()), state, self.base_path)


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

    def parse_list_item(self, item):
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

    def parse_list_item(self, item):
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

    def parse_list_item(self, item):
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
            # this also commits deletes
            return ['commit', '-a', '-m', message]

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


