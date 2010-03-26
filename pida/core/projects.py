# -*- coding: utf-8 -*-
"""
    pida.core.project
    ~~~~~~~~~~~~~~~~~~~~

    Project features for PIDA

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL2 or later
"""
from __future__ import with_statement
import os
from collections import defaultdict

from pida.core.log import Log
from pida.utils.path import get_relative_path
from pida.utils.addtypes import Enumeration
from glob import fnmatch

from pida.utils.puilder.model import Build

try:
    import cPickle as pickle
except ImportError:
    import pickle

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


#FIXME: win32 fixup
DATA_DIR = ".pida-metadata"
CACHE_NAME = "FILECACHE"

RESULT = Enumeration("RESULT",
            ("YES", "NO", "YES_NOCHILDS", "NO_NOCHILDS",
             "ABORT"))

REFRESH_PRIORITY = Enumeration("REFRESH_PRIORITY",
            (("PRE_FILECACHE", 400), ("FILECACHE", 350),
            ("POST_FILECACHE", 300), ("EARLY", 200), ("NORMAL", 100),
            ("LATE", 0)))


class RefreshCall(object):
    priority = REFRESH_PRIORITY.NORMAL
    call = None

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

class Project(Log):
    """
    A PIDA project.

    Functions:
     * dict-alike api (but it is NOT a dict

    """

    def __init__(self, source_dir):
        self.source_directory = source_dir
        self.name = os.path.basename(source_dir)
        self._cache = self._init_cache()
        self.__data = {}
        self.reload()

    def __getitem__(self, key):
        return self.__data[key]

    def get(self, key, default=None):
        return self.__data.get(key)

    def __setitem__(self, key, value):
        self.__data[key] = value

    def __contains__(self, key):
        return key in self.__data

    def reload(self):
        """Loads the project file"""
        self.build = Build.loadf(self.project_file)


        # every project has a cache directory, we ensure it exists
        if not os.path.isdir(self.data_dir):
            try:
                os.mkdir(self.data_dir)
            except OSError, err:
                self.log.exception(err)

        #XXX: this might need wrappers for reload
        for mod in self.__data.values():
            if hasattr(mod, 'reload'):
                mod.reload()

    @property
    def options(self):
        return self.build.options

    @property
    def targets(self):
        return self.build.targets

    @property
    def markup(self):
        return '<b>%s</b>\n%s' % (self.display_name, self.source_directory)

    def get_meta_dir(self, *args, **kwargs):
        path = Project.data_dir_path(self.source_directory, *args)
        if kwargs.get('mkdir', True):
            Project.create_data_dir(self.source_directory, *args)
        if 'filename' in kwargs:
            return os.path.join(path, kwargs['filename'])
        return path

    data_dir = property(get_meta_dir)

    @property
    def project_file(self):
        return os.path.join(self.data_dir, 'project.json')

    @property
    def display_name(self):
        return self.options.get('name', self.name)

    def set_display_name(self, name):
        self.options['name'] = name

    def get_relative_path_for(self, filename):
        return get_relative_path(self.source_directory, filename)

    @staticmethod
    def create_blank_project_file(name, project_directory):
        Project.create_data_dir(project_directory)
        file_path = Project.data_dir_path(project_directory, 'project.json')
        b = Build()
        b.options['name'] = name
        b.dumpf(file_path)
        return file_path

    @staticmethod
    def create_data_dir(project_directory, *args):
        try:
            os.makedirs(Project.data_dir_path(project_directory, *args))
        except OSError:
            pass

    @staticmethod
    def data_dir_path(project_directory, *args):
        return os.path.join(project_directory, DATA_DIR, *args)


    def load_cache(self):
        path = self.get_meta_dir(filename=CACHE_NAME)

        if os.path.isfile(path):
            try:
                fp = open(path)
                self._cache = pickle.load(fp)
                return True
            except Exception, err:
                self.log.error("can't load cache")
                os.unlink(path)
        return False

    def save_cache(self):
        path = self.get_meta_dir(filename=CACHE_NAME)
        try:
            fp = open(path, "w")
            pickle.dump(self._cache, fp)
            fp.close()
        except OSError, err:
            self.log.error("can't save cache: %s", err)

    @staticmethod
    def _init_cache():
        return {
                "paths": {},
                "dirs": {},
                "files": {},
                "filenames": defaultdict(list),
                "dirnames": defaultdict(list),
               }

    def _rebuild_shortcuts(self):
        self._cache["dirs"] = {}
        self._cache["files"] = {}
        self._cache["filenames"] = defaultdict(list)
        self._cache["dirnames"] = defaultdict(list)

        for info in self._cache["paths"].itervalues():
            if info.is_dir:
                self._cache["dirs"][info.relpath] = info
                self._cache["dirnames"][info.basename].append(info)
            elif info.is_file:
                self._cache["files"][info.relpath] = info
                self._cache["filenames"][info.basename].append(info)


    def index_path(self, path, update_shortcuts=True):
        """
        Update the index of a single file/directory

        @path is an absolute path
        """
        from pida.services.language import DOCTYPES
        doctype = DOCTYPES.type_by_filename(path)
        rel = self.get_relative_path_for(path)
        if rel is None:
            return
        rpath = os.sep.join(self.get_relative_path_for(path))

        if rpath is None:
            #document outside of project
            return
        if rpath in self._cache['paths']:
            info = self._cache['paths'][rpath]
        else:
            try:
                info = FileInfo(path, rpath)
            except OSError, err:
                self.log.info(_("Error indexing %s:%s") % (path, err))
                return
        info.doctype = doctype and doctype.internal or None
        self._cache["paths"][info.relpath] = info

        if update_shortcuts:
            if info.is_dir:
                if info not in self._cache["dirnames"][info.basename]:
                    self._cache["dirnames"][info.basename].append(info)
                self._cache["dirs"][info.relpath] = info
            if info.is_file:
                if info not in self._cache["filenames"][info.basename]:
                    self._cache["filenames"][info.basename].append(info)
                self._cache["files"][info.relpath] = info

        if info.dirname != info.basename:
            if not info.dirname in self._cache["paths"]:
                self.index(info.dirname, recrusive=False)
                self.log.info(_('Project refresh highly suggested'))
            self._cache["paths"][info.dirname].children[info.basename] = info

        return info

    def _del_info(self, info):
        """Delete info and all children if any recrusivly"""
        #raise Exception()
        if info.dirname:
            parent = self._cache['paths'][info.dirname]
            if info in parent.children:
                del parent.children[info.basename]

        if info.is_dir:
            match = "%s%s" % (info.relpath, os.path.sep)
            todel = []
            for key in self._cache['paths'].iterkeys():
                if key[:len(match)] == match:
                    todel.append(key)
            for key in todel:
                del self._cache['paths'][key]

        del self._cache['paths'][info.relpath]

    def index(self, path="", recrusive=False, rebuild=False):
        """
        Updates the Projects filelist.

        @path: relative path under project root, or absolute
        @recrusive: update recrusive under root
        """
        if path == "" and rebuild:
            self._cache = self._init_cache()

        if os.path.isabs(path):
            rpath = self.get_relative_path_for(path)
        else:
            rpath = os.path.join(self.source_directory, path)

        if os.path.isfile(rpath):
            return self.index_path(rpath)

        #creat the root node
        self.index_path(rpath, update_shortcuts=False)

        for dirpath, dirs, files in os.walk(rpath):
            current = self._cache['paths'][
                             os.sep.join(self.get_relative_path_for(dirpath))]
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
            self._rebuild_shortcuts()
        except RuntimeError:
            # this happens when a index process is running while a file
            # is saved in the project of a non indexed directory which will
            # index the directory and a dictionary changed size during iteration
            # will most likely raise. they are harmless
            pass

    def query(self, test):
        """
        Get results from the file index.

        The test function returns a value from the RESULT object.

        This is the most powerfull but slowest test.

        @test: callable which gets a FileInfo object passed and returns an int
        """
        paths = self._cache['paths'].keys()[:]
        paths.sort()
        skip = None
        for path in paths:
            if skip and path[:len(skip)] == skip:
                continue
            item = self._cache['paths'][path]
            res = test(item)
            if res == RESULT.YES or res == RESULT.YES_NOCHILDS:
                yield item

            if res == RESULT.NO_NOCHILDS or res == RESULT.YES_NOCHILDS:
                skip = "%s%s" % (path, os.path.sep)

            if res == RESULT.ABORT:
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
                lst = self._cache['dirnames'].keys()
                lst.sort()
                for item in lst:
                    if filename is None or \
                       match(item, filename):
                        for i in self._cache['dirnames'][item]:
                            yield i
            else:
                if filename in self._cache['dirnames']:
                    for i in self._cache['dirnames'][filename]:
                        yield i

        if files:
            if glob:
                lst = self._cache['filenames'].keys()
                lst.sort()
                for item in lst:
                    if filename is None or \
                       match(item, filename):
                        for i in self._cache['filenames'][item]:
                            yield i
            else:
                if filename in self._cache['filenames']:
                    for i in self._cache['filenames'][filename]:
                        yield i
    def __repr__(self):
        return "<Project %s>" % self.source_directory
