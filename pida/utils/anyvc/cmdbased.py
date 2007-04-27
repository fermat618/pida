"""
    Classes for Command based vcs's
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :license: BSD
"""

# How I would like to see this
#
# Listing is fine
# For actions we will have the following:
# get_diff_command(paths)
# get_commit_command(paths)
# etc



from bases import VCSBase, DVCSMixin
from subprocess import Popen, PIPE
from file import StatedPath as Path
from os import path 

def action(fn):
    """
    Wrapper decorator for vcs actions - it does most of the work
    """
    action = fn.__name__

    def action_method(self, run=getattr(fn, "run", True), **kw):
        if getattr(self, "no_" + action, False):
            raise NotImplementedError("action %s not implemented for %r"% (
                            action, 
                            self.__class__.__name__
                            ))
        if getattr(fn, "paths", False):
            paths = kw.pop("paths", [])
            paths = map(path.normpath,
                        map(path.abspath, paths))
             
        else:
            paths = []
        xparams = fn(self, **kw) or []
        command = self._get_command(action, xparams + paths) 
        if run:
            return self._run(command)
        else:
            return self._output_pipe(command)
    action_method.__name__ = action
    action_method.__dict__ = fn.__dict__
    action_method.__doc__ = fn.__doc__
    return action_method

def fp_action(fn):
    """
    decorator for actions wich need processed filenames
    """
    fn.paths = True
    return action(fn)

def xaction(**kw):
    def xaction_decorator(fn):
        for k,v in kw.iteritems():
            setattr(fn, k, v)
        return action(fn)
    return xaction_decorator

class CommandBased(VCSBase):
    """
    Base class for all command based rcs's
    """
    command_map = {}
    
    def __init__(self, path_):
        self.path = path.normpath( path.abspath(path_) )
        self.base_path = self._find_basepath()
    
    def _find_basepath(self):

        if hasattr(self,"detect_subdir"):
            dsd = self.detect_subdir
            if isinstance(dsd, basestring):
                dsd = [dsd]
            if isinstance(dsd,dict):
                dsd = dsd.keys()
            
            assert isinstance(dsd, list), \
                "detect_subdir classattribute must be a string, list or dict"
            
            act_path = self.path
            detected_path = None
            detected_sd = None
            op = None
            while act_path != op:
                for sd in dsd:
                    if path.exists( path.join(act_path, sd)):
                        detected_path = act_path
                        detected_sd = sd
                        # continue cause some vcs's 
                        # got the subdir in every path
                op = act_path
                act_path = path.dirname(act_path)
                
            if not detected_path:
                raise ValueError(
                        "VC Basepath for vc class %r"
                        "not found above %s"%(
                            type(self), 
                            self.path)
                        )

            if isinstance(self.detect_subdir, dict):
                self.cmd = self.detect_subdir[detected_sd]

            return detected_path

    def _output_proc(self, args=[]):
        if not args:
            raise ValueError("need a valid command")
        return Popen(args, stdout=PIPE, cwd=self.base_path, close_fds=True)
    
    def _output_str(self,args=[]):
        return self._output_proc(args).communicate()[0]

    def _output_pipe(self, args=[]):
        return self._output_proc(args).stdout

    def _output_iter(self, args=[]):
        return iter(self._output_pipe(args))
    
    def _run(self,args=[]):
        #for line in self._output_pipe(args):
        #    print line,
        return args

    def _get_command(self, action, args = []):
        action = getattr(self, action + "_cmd", action)
        if not isinstance(action, list):
            action = self.command_map.get(action, action)
        if not isinstance(action, list):
            action = [action]
        return [self.cmd] + action + args

    @fp_action
    def commit(self, message,**kw):
        """
        commits the workdirs changeset

        @param message: the commit message - necessary!
        """
        return ["-m" , message]
        

    @fp_action
    def diff(self, **kw): pass

    @action
    def update(self, revision=None, **kw):
        if revision:
            return ["-r", revision]

    @fp_action
    def status(self, **kw): pass

    @xaction(run=False, paths=True)
    def _list_impl(self, recursive,**kw):
        """
        the default implementation is only cappable of 
        recursive operation on the complete workdir

        rcs-specific implementations might support 
        non-recursive and path-specific listing
        """
        if not recursive:
            return self.non_recursive_param
    

class DCommandBased(CommandBased, DVCSMixin):
    """
    base class for all distributed command based rcs's
    """

    @action
    def sync(self, **kw): pass

    @action
    def pull(self, **kw): pass
    
    @action
    def push(self, **kw): pass


class Monotone(DCommandBased):
    
    detect_subdir = {
            '_MTN':'mtn', # new style
            'MT':'monotone', #old style
            }
    non_recursive_param = [] #XXX: fix this bug
    # monotone cant do paths and non-recursive
    _list_impl_cmd = "automate inventory".split()

    @xaction(run=False, paths=False)
    def _list_impl(self,**kw):
        pass

    multiple_heads = True
    
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

    def parse_list_item(self, item):
        state = self.statemap.get(item[:3], "none") 
        return Path(path.normpath(item[8:].rstrip()), state, self.base_path)

class Bazaar(DCommandBased):
    cmd = "bzr"
    detect_subdir = ".bzr"
    no_sync = True

    non_recursive_param = ["--non-recursive"]

    command_map= {
            '_list_impl': ["ls", "-v"],
            '_cache_impl': 'st',
            }

    statemap  = {
            "unknown:": 'none',
            "added:": 'new',
            "unchanged:": 'normal',
            "removed:": 'removed',
            "ignored:": 'ignored',
            "modified:": 'modified',
            "conflicts:": 'S.conflict' }
    
    @xaction(run=False)
    def _cache_impl(self, **kw):
        pass

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
    
    _list_impl_cmd = ["st", "--no-ignore"]
    
    non_recursive_param = ["-N"]

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
        state = item[0]
        file = item[7:].strip()
        return Path(file, self.state_map[state], self.base_path) 

class Mercurial(DCommandBased):
    cmd = "hg"
    detect_subdir = ".hg"
   
    non_recursive_param = [] # TODO: figure how to be non-recursive with hg
    _list_impl_cmd = ["status", "-A"]

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

    non_recursive_param = []
    
    _list_impl_cmd = ['whatsnew', '--boring', '--summary']

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

