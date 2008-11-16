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
from string import Template
from weakref import proxy

from pida.core.log import Log
from pida.utils.path import get_relative_path

from pida.utils.puilder.model import Build

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


#FIXME: win32 fixup
DATA_DIR = ".pida-metadata"

class Project(Log):
    """
    A PIDA project.

    Functions:
     * dict-alike api (but it is NOT a dict

    """

    def __init__(self, source_dir):
        self.source_directory = source_dir
        self.name = os.path.basename(source_dir)
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

    def has_key(self, key):
        return key in self.__data

    def reload(self):
        """Loads the project file"""
        self.build = Build.loadf(self.project_file)


        # every project has a cache directory, we ensure it exists
        if not os.path.isdir(self.data_dir):
            try:
                os.mkdir(self.data_dir)
            except OSError, e:
                self.log.exception(e)
                
        #XXX: this might need wrappers for reload
        for m in self.__data.values():
            if hasattr(m, 'reload'):
                m.reload()

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

