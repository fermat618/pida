
import os
import fnmatch
from collections import defaultdict
try:
    import cPickle as pickle
except ImportError:
    import pickle

from pida.core.log import Log

CACHE_NAME = "FILECACHE"


class Result(object):
    __slots__ = "accept", "recurse", "abort"

    def __init__(self, accept=True, recurse=True, abort=False):
        self.accept = accept
        self.recurse = recurse
        self.abort = abort


class FileInfo(object):
    def __init__(self, path, relpath):
        self.relpath = relpath
        self.basename = os.path.basename(relpath)
        self.dirname = os.path.dirname(relpath)
        self.ext = os.path.splitext(self.basename)[1]
        self.doctype = None
        self.is_dir = os.path.isdir(path)
        self.is_file = os.path.isfile(path)
        self.mtime = os.path.getmtime(path)
        self.children = {}

    def __repr__(self):
        return "<FileInfo %s >" % self.relpath


class Indexer(Log):
    def __init__(self, project):
        self.project = project
        self.reset_cache()

    def reset_cache(self):
        self.cache = {
                "paths": {},
                "dirs": {},
                "files": {},
                "filenames": defaultdict(list),
                "dirnames": defaultdict(list),
               }

    def save_cache(self):
        path = self.project.get_meta_dir(filename=CACHE_NAME)
        try:
            with open(path, "w") as fp:
                pickle.dump(self.cache, fp)
        except OSError, err:
            self.log.error("can't save cache: %s", err)

    def load_cache(self):
        path = self.project.get_meta_dir(filename=CACHE_NAME)
        if os.path.isfile(path):
            try:
                with open(path) as fp:
                    self.cache = pickle.load(fp)
                return True
            except Exception, err:
                self.log.error("can't load cache of %r", self)
                os.unlink(path)
        return False


    def rebuild_shortcuts(self):
        self.cache["dirs"] = {}
        self.cache["files"] = {}
        self.cache["filenames"] = defaultdict(list)
        self.cache["dirnames"] = defaultdict(list)

        for info in self.cache["paths"].itervalues():
            if info.is_dir:
                self.cache["dirs"][info.relpath] = info
                self.cache["dirnames"][info.basename].append(info)
            elif info.is_file:
                self.cache["files"][info.relpath] = info
                self.cache["filenames"][info.basename].append(info)

    def index_path(self, path, update_shortcuts=False):
        """
        Update the index of a single file/directory

        @path is an absolute path
        """
        from pida.services.language import DOCTYPES
        doctype = DOCTYPES.type_by_filename(path)
        rel = self.project.get_relative_path_for(path)
        if rel is None:
            return
        rpath = os.sep.join(self.project.get_relative_path_for(path))

        if rpath is None:
            #document outside of project
            return
        if rpath in self.cache['paths']:
            info = self.cache['paths'][rpath]
        else:
            try:
                info = FileInfo(path, rpath)
            except OSError, err:
                self.log.info(_("Error indexing %s:%s") % (path, err))
                return
        info.doctype = doctype and doctype.internal or None
        self.cache["paths"][info.relpath] = info

        if update_shortcuts:
            if info.is_dir:
                if info not in self.cache["dirnames"][info.basename]:
                    self.cache["dirnames"][info.basename].append(info)
                self.cache["dirs"][info.relpath] = info
            if info.is_file:
                if info not in self.cache["filenames"][info.basename]:
                    self.cache["filenames"][info.basename].append(info)
                self.cache["files"][info.relpath] = info

        if info.dirname != info.basename:
            if not info.dirname in self.cache["paths"]:
                self.index(info.dirname, recrusive=False)
                self.log.info(_('Project refresh highly suggested'))
            self.cache["paths"][info.dirname].children[info.basename] = info

        return info

    def _del_info(self, info):
        """Delete info and all children if any recrusivly"""
        #raise Exception()
        if info.dirname:
            parent = self.cache['paths'][info.dirname]
            if info in parent.children:
                del parent.children[info.basename]

        if info.is_dir:
            match = "%s%s" % (info.relpath, os.path.sep)
            todel = []
            for key in self.cache['paths'].iterkeys():
                if key[:len(match)] == match:
                    todel.append(key)
            for key in todel:
                del self.cache['paths'][key]

        del self.cache['paths'][info.relpath]


    def index(self, path="", recrusive=False, rebuild=False):
        """
        Updates the Projects filelist.

        @path: relative path under project root, or absolute
        @recrusive: update recrusive under root
        """

        if path == "" and rebuild:
            self.reset_cache()

        if os.path.isabs(path):
            rpath = self.project.get_relative_path_for(path)
        else:
            rpath = os.path.join(self.project.source_directory, path)

        if os.path.isfile(rpath):
            return self.index_path(rpath)

        #creat the root node
        self.index_path(rpath, update_shortcuts=False)

        for dirpath, dirs, files in os.walk(rpath):
            current = self.cache['paths'][
                             os.sep.join(self.project.get_relative_path_for(dirpath))]
            if not recrusive:
                del dirs[:]
            for file_ in files:
                if os.access(os.path.join(dirpath, file_), os.R_OK):
                    self.index_path(os.path.join(dirpath, file_),
                                    update_shortcuts=False)
            for dir_ in dirs:
                if os.access(os.path.join(dirpath, dir_), os.R_OK | os.X_OK):
                    self.index_path(os.path.join(dirpath, dir_),
                                    update_shortcuts=False)

            # delete not existing nodes
            #print current.children, files+dirs
            for old in [x for x in current.children if x not in files + dirs]:
                self._del_info(current.children[old])
            #match = "%s%s" %(current.relpath, os.path.sep)
            #for key, item in self._cache['paths'].iteritems():
            #    print key, match, key[:len(match)]
            #    if key[:len(match)] == match:
            #      if item.basename not in dirs and item.basename not in files:
                        #print "dell", key
                        #del self._cache[key]
        try:
            self.rebuild_shortcuts()
        except RuntimeError:
            # this happens when a index process is running while a file
            # is saved in the project of a non indexed directory which will
            # index the directory and a dictionary changed size during iteration
            # will most likely raise. they are harmless
            pass



    def query(self, test):
        """
        Get results from the file index.
        This is the most powerfull but slowest test.

        :param test:
            callable which gets a FileInfo object passed 
            and returns a :class:`Result` object
        """
        paths = sorted(self.cache['paths'])
        skip = None
        for path in paths:
            if skip and path[:len(skip)] == skip:
                continue
            item = self.cache['paths'][path]
            res = test(item)
            if res is None:
                # asume not accepted, but recurse on no result
                res = Result(accept=False, recurse=True)
            if res.accept:
                yield item

            if not res.recurse:
                skip = "%s%s" % (path, os.path.sep)

            if res.abort:
                break

    def query_basename(self, filename, glob=False, files=True, dirs=False,
                       case=False):
        """
        Get results from the file index. It looks only at the basename of entries.

        If files and directories are requested, directories are returned first

        @filename: pattern to search for or None for all
        @glob: pattern is a glob pattern, case insensitive
        @files: search for a file
        @dirs: search for a directory
        @case: if True a case sensetive glob is used
        """
        if case:
            match = fnmatch.fnmatchcase
        else:
            match = fnmatch.fnmatch

        if filename is None:
            glob = True

        if dirs:
            if glob:
                lst = sorted(self.cache['dirnames'])
                for item in lst:
                    if filename is None or \
                       match(item, filename):
                        for i in self.cache['dirnames'][item]:
                            yield i
            else:
                if filename in self.cache['dirnames']:
                    for i in self.cache['dirnames'][filename]:
                        yield i

        if files:
            if glob:
                lst = sorted(self.cache['filenames'])
                for item in lst:
                    if filename is None or \
                       match(item, filename):
                        for i in self.cache['filenames'][item]:
                            yield i
            else:
                if filename in self.cache['filenames']:
                    for i in self.cache['filenames'][filename]:
                        yield i
