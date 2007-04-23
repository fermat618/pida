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

__all__ = ["VCSBase","DVCSMixin"]

class VCSBase(object):
    """
    Base class for all vcs's
    remember not to use super in subclasses
    """
    
    def __init__(self, path):
        self._cache = None
        self.setup()
        self.path = path

    def parse_list_item(self, item):
        raise NotImplementedError

    def parse_cache_item(self, item, last_state):
        raise NotImplementedError

    def _cache_impl(self, paths=False, recursive=False):
        return [] # generating a result dataset is only necessary for messed up vcs's 

    def _list_impl(self, paths=False, recursive=False):
        raise NotImplementedError
    
    def cache(self, paths=None, recursive=False):
        self._cache={}
        state = "none"
        for i in self._cache_impl(paths = paths, recursive=recursive):
            path, state = self.parse_cache_item(i, state)
            if path is not None:
                self._cache[path] = state
    
    def list(self, paths=None, recursive=False):
        self.cache(paths = paths,recursive=recursive)
        for i in self._list_impl(paths = paths, recursive=recursive):
            parsed = self.parse_list_item(i)
            if parsed is not None:
                yield parsed

    def diff(self, paths=None):
        raise NotImplementedError
    
    def update(self, revision=None):
        raise NotImplementedError

    def commit(self, paths=None, message=None):
        raise NotImplementedError

    def revert(self, paths=None, missing=False):
        raise NotImplementedError

    def add(self, paths=None, recursive=False):
        raise NotImplementedError
    
    def drop(self, paths=None, execute=False, recursive=False):
        raise NotImplementedError

class DVCSMixin(object):

    def pull(self, locations=None):
        raise NotImplementedError

    def sync(self, locations=None):
        raise NotImplementedError

    def push(self, locations=None):
        raise NotImplementedError

