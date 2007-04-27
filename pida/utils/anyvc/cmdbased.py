"""
    Classes for Command based vcs's
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :license: BSD
"""

from bases import VCSBase, DVCSMixin
from subprocess import Popen, PIPE
from file import StatedPath as Path
from os import path 

class CommandBased(VCSBase):
    """
    Base class for all command based rcs's
    """
    
    def __init__(self, versioned_path):
        self.path = path.normpath( path.abspath(versioned_path) )
        self.base_path = self._find_basepath()
    
    def _find_basepath(self):
        dsd = self.detect_subdir
             
        act_path = self.path
        detected_path = None
        detected_sd = None
        op = None
        while act_path != op:
            if path.exists( path.join(act_path, self.detect_subdir)):
                detected_path = act_path
                # continue cause some vcs's 
                # got the subdir in every path
            op = act_path
            act_path = path.dirname(act_path)
                
        if not detected_path:
            raise ValueError(
                    'VC Basepath for vc class %r'
                    'not found above %s'%(
                        type(self), 
                        self.path)
                    )

        return detected_path

    def _execute_command(self, args, result_type=str, **kw):
        if not args:
            raise ValueError('need a valid command')
        ret = Popen( 
                [self.cmd] + args, 
                stdout=PIPE, 
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
        return ['commit'] + paths

    def get_diff_args(self, paths=(), **kw):
        return ['diff'] + paths
    
    def get_update_args(self, revision=None, **kw):
        if revision:
            return ['update', '-r', revision]
        else:
            return ['update']

    def get_status_args(self,**kw):
        return ['status']

    def get_list_args(self, **kw):
        raise NotImplementedError("%s doesnt implement list")
    
    def commit(self, **kw):
        args = self.get_commit_args(**kw)
        return self._execute_command(args, **kw)

    def diff(self, **kw):
        args = self.get_diff_args(**kw)
        return self._execute_command(args, **kw)

    def update(self, **kw):
        args = self.get_update_args(**kw)
        return self._execute_command(args, **kw)
    
    def status(self, **kw):
        args = self.get_status_args(**kw)
        return self._execute_command(args, **kw)

    def _list_impl(self, recursive,**kw):
        """
        the default implementation is only cappable of 
        recursive operation on the complete workdir

        rcs-specific implementations might support 
        non-recursive and path-specific listing
        """
        args = self.get_list_args(**kw)
        return self._execute_command(args, result_type=file, **kw)

class CachedCommandMixin(object):
    def _cache_impl(self,**kw):
        args = self.get_cache_args(**kw)
        return self._execute_command(args, **kw)

class DCommandBased(CommandBased, DVCSMixin):
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

    def get_list_args(self, **kw):
        return ["automate", "inventory"]

    def parse_list_item(self, item):
        state = self.statemap.get(item[:3], "none") 
        return Path(path.normpath(item[8:].rstrip()), state, self.base_path)

class Bazaar(CachedCommandMixin,
             DCommandBased):
    cmd = "bzr"
    detect_subdir = ".bzr"
   
    def get_list_args(self, recursive=True, paths=(),**kw):
        ret = ["ls","-v"]
        if not recursive:
            ret.append("--non-recursive")
        ret.extend(paths)
        return ret
    
    def get_cache_args(self, *kw):
        return ["st"]

    statemap  = {
            "unknown:": 'none',
            "added:": 'new',
            "unchanged:": 'normal',
            "removed:": 'removed',
            "ignored:": 'ignored',
            "modified:": 'modified',
            "conflicts:": 'conflict' }
    
    def parse_cache_item(self, item, actstate):
        item = item.rstrip()
        newstate = self.statemap.get(item, None)
        if newstate is not None:
            return None, newstate
        elif item.startswith("  "):
            return item.strip(), actstate
        
        print "XXX-item", item, actstate
        return None, actstate
    
    def parse_list_item(self, item):
        if item.startswith("I"):
            return Path(item[1:].strip(), 'ignored', self.base_path)
        else:
            fn = item[1:].strip()
            return Path(
                fn, 
                self._cache.get(fn, 'normal'),
                self.base_path)

      


class SubVersion(CommandBased):
    cmd = "svn"
    detect_subdir = ".svn"
    
    def get_list_args(self, recursive=True, **kw):
        ret = ["st", "--no-ignore", "--ignore-externals"]
        if not recursive:
            ret.append("--non-recursive")
        return ret
    
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
            } 
    def parse_list_item(self, item):
        #TODO: output for external references broken
        if item == '\n':
            return
        state = item[0]
        file = item[7:].strip()
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

    cmd = 'darcs'

    detect_subdir = '_darcs'

    
    def get_list_cmd(self, **kw):
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
        elements = item.split(1)
        state = self.state_map[elements[0]]
        file = path.normpath(elements[1])
        return Path(file, state, self.base_path)

