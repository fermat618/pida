# -*- coding: utf-8 -*-
"""
    :copyright: 2009 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

Abstraction to get informations about processes etc...

"""
import os, sys

try:
    import psutil
except ImportError:
    psutil = None


if sys.platform != 'win32':
    def get_default_system_shell():
        """
        Returns the default shell for the user
        """
        import pwd
        return os.environ.get(
            'SHELL', # try shell from env
            pwd.getpwuid(os.getuid())[-1] # fallback to login shell
        )
    
    PATH_MATCHES = \
             ((r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(\:[0-9]+)?)',
               r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(\:[0-9]+)?)'),
              (r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+)',
               r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+)')
             )
else:
    #FIXME: win32 port
    def get_default_system_shell():
        """
        Returns the default shell for the user
        """
        return ""

    PATH_MATCHES = ()



if psutil and psutil.Process.getcwd:
    def get_cwd(pid):
        """
        Returns the working path for a process
    
        @pid: process id
        """
        try:
            return psutil.Process(pid).getcwd()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_absolute_path(path, pid):
        """
        Returns the absolut path for a path relative for the process pid
    
        @path: path to add
        @pid: process id
        """
        if os.path.isabs(path):
            return path
        try:
            base = psutil.Process(pid).getcwd()
            return os.path.abspath(os.path.join(base, path))
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            return path

elif sys.platform == 'linux2':
    # linux fallbacks
    def get_cwd(pid):
        """
        Returns the working path for a process
    
        @pid: process id
        """
        try:
            return os.readlink('/proc/%s/cwd'%pid)
        except OSError:
            return None

    def get_absolute_path(path, pid):
        """
        Returns the absolut path for a path relative for the process pid
    
        @path: path to add
        @pid: process id
        """
        #XXX: works on bsd and linux only
        #     solaris needs /proc/%s/path/cwd
        if os.path.isabs(path):
            return path
        try:
            base = os.readlink('/proc/%s/cwd'%pid)
            return os.path.abspath(os.path.join(base, path))
        except OSError:
            return path

else:
    def get_cwd(dummy):
        """
        Returns the working path for a process

        !!! NOOP FALLBACK !!!

        @pid: process id
        """
        return ''

    def get_absolute_path(path, dummy):
        """
        Returns the absolut path for a path relative for the process pid

        !!! NOOP FALLBACK !!!

        @path: path to add
        @pid: process id
        """
        return path

