# -*- coding: utf-8 -*-
"""
    :copyright: 2009 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

Abstraction to get informations about processes etc...

"""
import os, sys

try:
    import psutil
    NoSuchProcess = psutil.NoSuchProcess
    AccessDenied = psutil.AccessDenied
except ImportError:
    psutil = None
    class NoSuchProcess(Exception):
        """
        No process was found for the given parameters.
        """
        pass
    class AccessDenied(Exception):
        """
        No process was found for the given parameters.
        """
        pass



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
             ((r'((\.\.\/|[-\.~a-zA-Z0-9_/\-\\])*(\.[a-zA-Z0-9]+)*(\:[0-9]+)?)',
               r'((\.\.\/|[-\.~a-zA-Z0-9_/\-\\])*(\.[a-zA-Z0-9]+)*(\:[0-9]+)?)'),
             )
# old versions
#            (r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\(.[a-zA-Z0-9]+){0,1})',
#              r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.([a-zA-Z0-9]+){0,1})')
# 	         ((r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(\:[0-9]+)?)',
#              r'((\.\./|[-\.~a-zA-Z0-9_/\-\\])*\.[a-zA-Z0-9]+(\:[0-9]+)?)'),

else:
    #FIXME: win32 port
    def get_default_system_shell():
        """
        Returns the default shell for the user
        """
        return ""

    PATH_MATCHES = ()



if psutil and hasattr(psutil.Process, 'getcwd'):
    def get_cwd(pid):
        """
        Returns the working path for a process
    
        @pid: process id
        """
        return psutil.Process(pid).getcwd()

    def get_absolute_path(path, pid):
        """
        Returns the absolut path for a path relative for the process pid
    
        @path: path to add
        @pid: process id
        """
        if os.path.isabs(path):
            return path
        base = psutil.Process(pid).getcwd()
        return os.path.abspath(os.path.join(base, path))

elif sys.platform in ('linux2', 'bsd'):
    # linux fallbacks
    def get_cwd(pid):
        """
        Returns the working path for a process
    
        @pid: process id
        """
        try:
            return os.readlink('/proc/%s/cwd'%pid)
        except OSError:
            raise NoSuchProcess("pid %s does not exist" %pid)

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
            raise NoSuchProcess("pid %s does not exist" %pid)

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
        if os.path.isabs(path):
            return path

        return None

if psutil:
    def pid_exist(pid):
        """
        Check whether the given PID exists in the current process list
        """
        return psutil.pid_exists(pid)

elif sys.platform in ('linux2', 'bsd'):
    def pid_exist(pid):
        """
        Check whether the given PID exists in the current process list
        """
        return os.path.exists("/proc/%s" %pid)
else:
    def pid_exist(dummy):
        """
        Check whether the given PID exists in the current process list
        """
        return None


if psutil:
    def kill_pid(pid, sig=None):
        """
        Kill the current process by using signal sig (defaults to SIGKILL).
        """
        psutil.Process(pid).kill(sig)

elif hasattr(os, 'kill'):
    def kill_pid(pid, sig=None):
        """
        Kill the current process by using signal sig (defaults to SIGKILL).
        """
        if sig is not None:
            try:
                return os.kill(pid, sig)
            except OSError, err:
                raise NoSuchProcess(err)
        else:
            try:
                return os.kill(pid, 9)
            except OSError, err:
                raise NoSuchProcess(err)
else:
    def kill_pid(dummy, dummy2=None):
        """
        Kill the current process by using signal sig (defaults to SIGKILL).
        """
        return None

