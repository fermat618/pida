# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2006 Ali Afshar aafshar@gmail.com

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from zope.interface import Interface, Attribute


class ILocalVCS(Interface):
    """a high level interface to local vcs operations on a
    revision controlled directory
    """

    def configure():## do in init
        """Set up the instace for the actual vcs"""

    def is_in(dir):
        """determine if a directory is managed by the implementing vcs"""
    
    def parse_list_item(item):
        """item is a rcs-specidic file entry, returns a stated file"""

    def _list_impl(paths=None, recursive=None):
        """ iterate over vcs specifiv file entries"""

    def list(paths=None, recursive=False):
        """return an iterator over stated files"""
    
    def diff(paths=None):
        """differences of all files below the paths"""
    
    def update():
        """update to the most recent revision"""

    def commit(paths=None):
        """commit all changes of files below the paths

        - might be a network operation"""

    def revert(paths=None, missing=False):
        """revert all changes in files below the paths
        
        - if missing is True only restore deleted files wich are still in
          revision controll"""

    def add(paths=None, recursive=False):
        """adds all paths to version controll
        
        - if recursive is True add all 
          files/directories below paths to the rcs"""

    def drop(paths=None, execute=False, recursive=False):
        """removes a path from version-controll
        if its not recursive it will fail on directories wich contain versioned
        files

        params:
          execute -- also remove the files from the local filesystem
          recursive -- recurse a directory tree - use with caution
        """

class IDistributedVCS(ILocalVCS):
    """high level operations on distributed vcs's"""

    def pull(locations=None):
        """pulls from locations or default"""

    def sync(locations=None):
        """sync with locations or default"""

    def push(locations=None):
        """push to loations or default"""
