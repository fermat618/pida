from cmdbased import DCommandBased, relative_to, Path
import os.path

class Monotone(DCommandBased):

    cmd = 'mtn'
    detect_subdir = '_MTN'

    def __init__(self, versioned_path):
        DCommandBased.__init__(self, versioned_path)
        self.interface_version = float(
                self.execute_command(['au','interface_version']))

    def process_paths(self, paths):
        return map(relative_to(self.base_path), paths)

    def get_remove_args(self, paths, **kw):
        return ['drop'] + self.process_paths(paths)

    def get_list_args(self, paths=(), recursive=True, **kw):
        cmd = ['automate', 'inventory']
        if self.interface_version >= 6:
            # we got a recent version with better features
            if not recursive:
                cmd.extend(['--depth', '0'])
            cmd.extend(self.process_paths(paths))
        return cmd

    def parse_list_item(self, item, cache):
        state = self.statemap.get(item[:3], 'none')
        return Path(os.path.normpath(item[8:].rstrip()), state, self.base_path)

    def parse_list_items(self, items, cache):
        if self.interface_version < 6:
            return (self.parse_list_item(item, cache) for item in items)
        else:
            return self.parse_basic_io(items)

    def parse_basic_io(self, iter):
        """
        .. warning::
            * this doesnt parse correct, just the minimal work to get the status info
            * no support for filenames with spaces 
            * no complete status handling yet
        """
        for info in self.parse_basic_io_dicts(iter):
            stats = info['status']
            path = info['path'][0]
            changes = info.get('changes', [])

            if not path or path == '.':
                continue

            #XXX: REALLY RECHECK THIS !!!!
            # print path, stats, changes

            if 'rename_source' in stats and not 'rename_target' in stats:
                continue

            if 'invalid' in stats:
                status = 'error'
            elif 'content' in changes or 'rename_target' in changes:
                status = 'modified'
            elif 'known' in stats:
                status = 'normal'
            elif 'unknown' in stats:
                if 'dropped' in stats:
                    status = 'removed'
                else:
                    status = 'unknown'
            elif 'ignored' in stats:
                status = 'ignored'
            elif 'missing' in stats:
                status = 'missing'
            else:
                status = 'error'


            yield Path(path, status, self.base_path)

    def parse_basic_io_dicts(self, iter):
        res = {}
        for line in iter:
            line = line.strip().split()
            if line:
                res[line[0]] = [x.strip('"') for x in line[1:]]
            else:
                yield res
                res = {}
    
    # for monotone prior to 0.37
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

