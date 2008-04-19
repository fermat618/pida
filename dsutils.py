import sys
import os
from commands import getstatusoutput, getoutput

def pkgc_version_check(name, longname, req_version):
    is_installed = not os.system('pkg-config --exists %s' % name)
    if not is_installed:
        print "Could not find %s" % longname
        return 0

    orig_version = getoutput('pkg-config --modversion %s' % name)
    version = map(int, orig_version.split('.'))
    pkc_version = map(int, req_version.split('.'))

    if version >= pkc_version:
        return True
    else:
        print "Warning: Too old version of %s" % longname
        print "         Need %s, but %s is installed" % \
              (pkc_version, orig_version)
        return False

def pkc_get_dirs(names, option, flag):
    retval = []
    for name in names:
        output = getoutput(' '.join(['pkg-config', option, name]))
        retval.extend(output.replace(flag, '').split())
    return retval

def pkc_get_include_dirs(*names):
    return pkc_get_dirs(names, '--cflags-only-I', '-I')

def pkc_get_libraries(*names):
    return pkc_get_dirs(names, '--libs-only-l', '-l')

def pkc_get_library_dirs(*names):
    return pkc_get_dirs(names, '--libs-only-L', '-L')
