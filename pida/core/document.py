# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005 Ali Afshar aafshar@gmail.com

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

import os
import mimetypes
import stat
import gobject
import base
import time

from charfinder import DETECTOR_MANAGER
import codecs

import actions


class document_handler(actions.action_handler):
    
    globs = []
    type_name = 'document'

    def init(self):
        self.__filenames = {}
        self.__docids = {}

    def create_document(self, filename):
        pass

    def view_document(self, document):
        pass

def relpath(target, basepath=os.curdir):
    """
    Return a relative path to the target from either the current dir or an
    optional base dir. Base can be a directory specified either as absolute
    or relative to current dir.
    """

    if not os.path.exists(target):
        raise OSError, 'Target does not exist: '+target

    if not os.path.isdir(basepath):
        raise OSError, 'Base is not a directory or does not exist: '+basepath

    base_list = (os.path.abspath(basepath)).split(os.sep)
    target_list = (os.path.abspath(target)).split(os.sep)

    # On the windows platform the target may be on a completely different
    # drive from the base.
    if os.name in ['nt', 'dos', 'os2'] and base_list[0] != target_list[0]:
        msg = 'Target is on a different drive to base. Target: %s, base: %s'
        msg %= (target_list[0].upper(), base_list[0].upper())
        raise OSError(msg)

    # Starting from the filepath root, work out how much of the filepath is
    # shared by base and target.
    for i in range(min(len(base_list), len(target_list))):
        if base_list[i] != target_list[i]:
            break
    else:
        # If we broke out of the loop, i is pointing to the first differing
        # path elements. If we didn't break out of the loop, i is pointing to
        # identical path elements. Increment i so that in all cases it points
        # to the first differing path elements.
        i+=1

    rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:-1]
    if rel_list:
        rel_list = rel_list + ['']
        return os.path.join(*rel_list)
    else:
        return ''

new_file_index = 1


class document(base.pidacomponent):
    """Base document class."""
    """A real file on disk."""
    icon_name = 'new'

    markup_prefix = ''
    markup_directory_color = '#0000c0'
    markup_attributes = ['project_name', 'project_relative_path', 'basename',
                         'directory_colour']
    markup_string = ('<span color="#600060">'
                     '%(project_name)s</span><tt>:</tt>'
                     '<span color="%(directory_colour)s">'
                     '%(project_relative_path)s</span>'
                     '<b>%(basename)s</b>')
    contexts = []
    is_new = False

    def __init__(self, filename=None,
                       markup_attributes=None,
                       markup_string=None,
                       contexts=None,
                       icon_name=None,
                       handler=None,
                       detect_encoding=DETECTOR_MANAGER):
        self.__handler = handler
        self.__filename = filename
        self.__unique_id = time.time()
        self.__project = None
        self.__newfile_index = None
        self.__detect_encoding = detect_encoding
        
        if filename is None:
            global new_file_index
            self.__newfile_index = new_file_index
            new_file_index =  new_file_index + 1
        if markup_attributes is not None:
            self.markup_attributes = markup_attributes
        if markup_string is not None:
            self.markup_string = markup_string
        base.pidacomponent.__init__(self)
                     
    def init(self):
        self.__reset()

    def __reset(self):
        self.__lines = None
        self.__string = None
        self.__stat = None
        self.__mimetype = None
        self.__encoding = None
        
    reset = __reset
        
    def __load(self):
        if self.__filename is None:
            return

        if self.__stat is None:
            self.__stat = self.__load_stat()
        if self.__mimetype is None:
            self.__mimetype = self.__load_mimetype()
        
        #if self.__encoding is not None:
            # Loading was already found, we're done
        #AA we like to load again!!
            #assert self.__string is not None
            #assert self.__lines is not None
            #return
        
        # lines and string depend on encoding
            
        try:
            stream = open(self.__filename, "rb")
            try:
                fname = self.__filename
                mime = self.__mimetype
                self.__encoding = self.__detect_encoding(stream, fname, mime)
                stream.seek(0)
                stream = codecs.EncodedFile(stream, self.__encoding)
                self.__lines = list(stream)
                self.__string = "".join(self.__lines)
            finally:
                stream.close()
        except IOError:
            # When there's a problem set the encoding to None and the rest too
            self.__encoding = None
            self.__lines = None
            self.__string = None
            raise
            # Also warn the log about it
            self.log.warn('failed to open file %s', self.filename)
            
        
    def __load_stat(self):
        try:
            stat_info = os.stat(self.__filename)
        except OSError:
            stat_info = None
        return stat_info

    def __load_mimetype(self):
        typ, encoding = mimetypes.guess_type(self.__filename)
        if typ is None:
            mimetype = ('', '')
        else:
            mimetype = tuple(typ.split('/'))
        return mimetype

    def __iter__(self):
        self.__load()
        return iter(self.__lines)

    def get_lines(self):
        return self.__iter__()

    lines = property(get_lines)

    def __len__(self):
        self.__load()
        return self.__stat[stat.ST_SIZE]

    length = property(__len__)
    
    def __get_string(self):
        self.__load()
        return self.__string

    string = property(__get_string)
        
    def __get_stat(self):
        self.__stat = self.__load_stat()
        return self.__stat

    stat = property(__get_stat)

    def __get_mimetype(self):
        return self.__mimetype

    mimetype = property(__get_mimetype)

    __encoding = None
    def get_encoding(self):
        self.__load()
        return self.__encoding
    
    encoding = property(get_encoding)
    
    def get_directory(self):
        return os.path.dirname(self.filename)
    directory = property(get_directory)

    def get_directory_basename(self):
        return os.path.basename(self.directory)

    directory_basename = property(get_directory_basename)

    def get_basename(self):
        return os.path.basename(self.filename)

    basename = property(get_basename)

    def get_directory_colour(self):
        return self.markup_directory_color
    directory_colour = property(get_directory_colour)

    def poll(self):
        self.__load()
        new_stat = self.__load_stat()
        if new_stat is None:
            return False
        if new_stat.st_mtime != self.__stat.st_mtime:
            self.__stat = new_stat
            self.__reset()
            return True
        else:
            return False

    def poll_until_change(self, callback, delay=1000):
        def do_poll():
            poll = self.poll()
            if poll:
                callback()
                return False
            else:
                return True
        gobject.timeout_add(delay, do_poll)

    def get_filename(self):
        return self.__filename

    def set_filename(self, filename):
        self.__filename = filename

    filename = property(get_filename, set_filename)

    def get_unique_id(self):
        return self.__unique_id
    unique_id = property(get_unique_id)

    def get_markup(self):
        prefix = '<b><tt>%s </tt></b>' % self.markup_prefix
        if self.filename is not None:
            s = self.markup_string % self.__build_markup_dict()
        else:
            s = '<b>New File %s</b>' % self.__newfile_index
        return '%s%s' % (prefix, s)
    markup = property(get_markup)

    def __build_markup_dict(self):
        markup_dict = {}
        for attr in self.markup_attributes:
            markup_dict[attr] = getattr(self, attr)
        return markup_dict

    def get_handler(self):
        return self.__handler
    handler = property(get_handler)

    def get_project_name(self):
        if self.__project:
            return self.__project.general__name
        else:
            return ''
    project_name = property(get_project_name)

    def get_project_relative_path(self):
        if self.__project:
            return relpath(self.filename, self.__project.source__directory)
        else:
            return os.path.join(self.directory_basename, '')

    project_relative_path = property(get_project_relative_path)
    
    def set_project(self, project):
        self.__project = project

    def get_is_new(self):
        return self.filename is None

    is_new = property(get_is_new)

    def get_newfile_index(self):
        return self.__newfile_index
    
    newfile_index = property(get_newfile_index)
        
class DocumentCache(object):
    
    def __init__(self, result_call):
        self._get_result = result_call
        self._cache = {}
        
    def get_result(self, document):
        try:
            result, mtime = self._cache[document.unique_id]
        except KeyError:
            result = mtime = None
        docmtime = document.stat.st_mtime
        if docmtime != mtime:
            result = self._get_result(document)
            self._cache[document.unique_id] = (result, docmtime)
        return result
        

import unittest

class DocumentCacheTest(unittest.TestCase):

    def setUp(self):
        self.calls = 0
        def call(doc):
            self.calls += 1
            return 1
        self.cache = DocumentCache(call)
        class MockD:
            class stat:
                m_time = 1
            unique_id = 1
        self.doc = MockD()

    def test_get(self):
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.cache.get_result(self.doc), 1)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.cache.get_result(self.doc), 1)
        self.assertEqual(self.calls, 1)
        self.doc.stat.m_time = 2
        self.assertEqual(self.cache.get_result(self.doc), 1)
        self.assertEqual(self.calls, 2)

def test():
    unittest.main()
    
        
class realfile_document(document):
    """Real file"""



