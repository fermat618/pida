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
        self.setup()
        self.path = path

    def parse_list_items(self, items, cache):
        """
        redirect to parse_list_item
        a more complex parser might need to overwrite
        """
        for item in items:
            rv = self.parse_list_item(item, cache)
            if rv: yield rv

    def parse_list_item(self, item, cache):
        """
        parse a single listing item
        """
        raise NotImplementedError

    def parse_cache_items(self, items):
        """
        parses vcs specific cache items to a list of (name, state) tuples
        """
        return []

    def cache_impl(self, paths=False, recursive=False):
        """
        creates a list of vcs specific cache items
        only necessary by messed up vcs's

        in case of doubt - dont touch ^^
        """
        return []

    def list_impl(self, paths=False, recursive=False):
        """
        yield a list of vcs specific listing items
        """
        raise NotImplementedError
    
    def cache(self, paths=(), recursive=False):
        """
        return a mapping of name to cached states
        only necessary for messed up vcs's
        """
        return dict(
                self.parse_cache_items(
                self.cache_impl(
                    paths = paths,
                    recursive=recursive
                    )))
    
    def list(self, paths=(), recursive=False):
        """
        yield a list of Path instances tagged with status informations
        """
        cache = self.cache(paths = paths,recursive=recursive)
        return self.parse_list_items(
                self.list_impl(
                    paths = paths, 
                    recursive=recursive, 
                    ), cache)

    def diff(self, paths=()):
        raise NotImplementedError
    
    def update(self, revision=None):
        raise NotImplementedError

    def commit(self, paths=None, message=None):
        raise NotImplementedError

    def revert(self, paths=None, missing=False):
        raise NotImplementedError

    def add(self, paths=None, recursive=False):
        raise NotImplementedError
    
    def remove(self, paths=None, execute=False, recursive=False):
        raise NotImplementedError

class DVCSMixin(object):

    def pull(self, locations=None):
        raise NotImplementedError

    def sync(self, locations=None):
        raise NotImplementedError

    def push(self, locations=None):
        raise NotImplementedError

