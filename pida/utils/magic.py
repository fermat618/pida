"""
magic is a wrapper around the libmagic file identification library.

upstream: http://hupp.org/adam/hg/python-magic/

Distributed under the PSF License: http://www.python.org/psf/license/ 

See README for more information.

Usage:

>>> import magic
>>> magic.from_file("testdata/test.pdf")
'PDF document, version 1.2'
>>> magic.from_file("testdata/test.pdf", mime=True)
'application/pdf'
>>> magic.from_buffer(open("testdata/test.pdf").read(1024))
'PDF document, version 1.2'
>>>


"""


import os.path
import ctypes
import ctypes.util

from ctypes import c_char_p, c_int, c_size_t, c_void_p

from threading import RLock

MAGIC_LOCK = RLock()

class MagicException(Exception): pass

class Magic:
    """
    Magic is a wrapper around the libmagic C library.  
    
    This class is threadsafe
    """

    def __init__(self, mime=False, magic_file=None, flags=None):
        """
        Create a new libmagic wrapper.

        mime - if True, mimetypes are returned instead of textual descriptions
        magic_file - use a mime database other than the system default
        
        """
        if not flags:
            flags = MAGIC_NONE
        
        if mime:
            flags |= MAGIC_MIME
        try:
            MAGIC_LOCK.acquire()
            cookie = None
            while cookie is None:
                cookie = magic_open(flags)
            self.cookie = cookie

            if magic_load(self.cookie, magic_file):
                raise ValueError("Can't load magic")
        finally:
            MAGIC_LOCK.release()


    def from_buffer(self, buf):
        """
        Identify the contents of `buf`
        """
        try:
            MAGIC_LOCK.acquire()
            rv = magic_buffer(self.cookie, buf)
        finally:
            MAGIC_LOCK.release()
        return rv
            

    def from_file(self, filename):
        """
        Identify the contents of file `filename`
        raises IOError if the file does not exist
        """

        if not os.path.exists(filename):
            raise IOError("File does not exist: " + filename)
        try:
            MAGIC_LOCK.acquire()
            rv = magic_file(self.cookie, filename)
        finally:
            MAGIC_LOCK.release()
        return rv

    def __del__(self):
        try:
            MAGIC_LOCK.acquire()
            magic_close(self.cookie)
        except Exception, e:
            # it's to late to do anything here anyway.
            # it seems to report random but seldom errors here
            pass
        finally:
            MAGIC_LOCK.release()


_magic_mime = None
_magic = None

def _get_magic_mime():
    global _magic_mime
    if not _magic_mime:
        _magic_mime = Magic(mime=True)
    return _magic_mime

def _get_magic():
    global _magic
    if not _magic:
        _magic = Magic()
    return _magic

def _get_magic_type(mime):
    if mime:
        return _get_magic_mime()
    else:
        return _get_magic()

def from_file(filename, mime=False):
    """
    Return magic from file
    
    This function is NOT threadsafe.
    """
    m = _get_magic_type(mime)
    return m.from_file(filename)

def from_buffer(buffer, mime=False):
    """
    Return magic from buffer
    
    This function is NOT threadsafe.
    """
    m = _get_magic_type(mime)
    return m.from_buffer(buffer)




libmagic = ctypes.CDLL(ctypes.util.find_library('magic'))

magic_t = ctypes.c_void_p

def errorcheck(result, func, args):
    try:
        MAGIC_LOCK.acquire()
        err = magic_errno(args[0])
    finally:
        MAGIC_LOCK.release()
    if err is not 0:
        raise MagicException('error no %s' %err)
    else:
        return result


magic_open = libmagic.magic_open
magic_open.restype = magic_t
magic_open.argtypes = [c_int]

magic_close = libmagic.magic_close
magic_close.restype = None
magic_close.argtypes = [magic_t]
magic_close.errcheck = errorcheck

magic_error = libmagic.magic_error
magic_error.restype = c_char_p
magic_error.argtypes = [magic_t]

magic_errno = libmagic.magic_errno
magic_errno.restype = c_int
magic_errno.argtypes = [magic_t]

magic_file = libmagic.magic_file
magic_file.restype = c_char_p
magic_file.argtypes = [magic_t, c_char_p]
magic_file.errcheck = errorcheck


_magic_buffer = libmagic.magic_buffer
_magic_buffer.restype = c_char_p
_magic_buffer.argtypes = [magic_t, c_void_p, c_size_t]
_magic_buffer.errcheck = errorcheck


def magic_buffer(cookie, buf):
    return _magic_buffer(cookie, buf, len(buf))


magic_load = libmagic.magic_load
magic_load.restype = c_int
magic_load.argtypes = [magic_t, c_char_p]
magic_load.errcheck = errorcheck

magic_setflags = libmagic.magic_setflags
magic_setflags.restype = c_int
magic_setflags.argtypes = [magic_t, c_int]

magic_check = libmagic.magic_check
magic_check.restype = c_int
magic_check.argtypes = [magic_t, c_char_p]

magic_compile = libmagic.magic_compile
magic_compile.restype = c_int
magic_compile.argtypes = [magic_t, c_char_p]



MAGIC_NONE = 0x000000 # No flags

MAGIC_DEBUG = 0x000001 # Turn on debugging

MAGIC_SYMLINK = 0x000002 # Follow symlinks

MAGIC_COMPRESS = 0x000004 # Check inside compressed files

MAGIC_DEVICES = 0x000008 # Look at the contents of devices

MAGIC_MIME = 0x000010 # Return a mime string

MAGIC_CONTINUE = 0x000020 # Return all matches

MAGIC_CHECK = 0x000040 # Print warnings to stderr

MAGIC_PRESERVE_ATIME = 0x000080 # Restore access time on exit

MAGIC_RAW = 0x000100 # Don't translate unprintable chars

MAGIC_ERROR = 0x000200 # Handle ENOENT etc as real errors

MAGIC_NO_CHECK_COMPRESS = 0x001000 # Don't check for compressed files

MAGIC_NO_CHECK_TAR = 0x002000 # Don't check for tar files

MAGIC_NO_CHECK_SOFT = 0x004000 # Don't check magic entries

MAGIC_NO_CHECK_APPTYPE = 0x008000 # Don't check application type

MAGIC_NO_CHECK_ELF = 0x010000 # Don't check for elf details

MAGIC_NO_CHECK_ASCII = 0x020000 # Don't check for ascii files

MAGIC_NO_CHECK_TROFF = 0x040000 # Don't check ascii/troff

MAGIC_NO_CHECK_FORTRAN = 0x080000 # Don't check ascii/fortran

MAGIC_NO_CHECK_TOKENS = 0x100000 # Don't check ascii/tokens
