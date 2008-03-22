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

from pida.utils.descriptors import cached_property

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

new_file_index = 1


class Document(object):
    """Base document class.

    Represents a file on disk.
    """
    icon_name = 'new'

    markup_prefix = ''
    markup_directory_color = '#0000c0'
    markup_attributes = ['project_name', 'project_relative_path', 'basename',
                         'directory_colour']
    markup_string = ('<span color="#600060">'
                     '%(project_name)s</span><tt>:</tt>'
                     '<span color="%(directory_colour)s">'
                     '%(project_relative_path)s/</span>'
                     '<b>%(basename)s</b>')
    def __init__(self, boss, filename=None,
                       markup_attributes=None,
                       markup_string=None,
                       contexts=None,
                       icon_name=None,
                       handler=None,
                       detect_encoding=DETECTOR_MANAGER):
        self.boss = boss
        self._handler = handler
        self.filename = filename
        self.project = None
        self._detect_encoding = detect_encoding
        self.creation_time = time.time()
        
        if filename is None:
            global new_file_index
            self.newfile_index = new_file_index
            new_file_index = new_file_index + 1
        else:
            self.newfile_index = None

        if markup_attributes is not None:
            self.markup_attributes = markup_attributes
        if markup_string is not None:
            self.markup_string = markup_string

        self.project, self.project_relative_path = self.get_project_relative_path()
        self.clear()

    def clear(self):
        self._str = None
        self._lines = None
        self._encoding = None
        self._last_mtime = None

    def _load(self):
        """loads the document content/encoding

        sets the attributes _str, _lines and _encoding
        """

        if self.filename is None or self.modified_time == self._last_mtime:
            return


        # lines and string depend on encoding
        stream = None
        try:
            stream = open(self.filename, "rb")
            fname = self.filename
            mime = self.mimetype

            self._encoding = self._detect_encoding(stream, fname, mime)
            stream.seek(0)
            stream = codecs.EncodedFile(stream, self._encoding)
            self._str = stream.read()
            self._lines = self._str.splitlines()
        except:
            if stream is not None:
                stream.close()
            # When there's a problem set the encoding to None and the rest too
            self.clear()
            # Also warn the log about it
            self.boss.log.warn(_('failed to open file %s'), self.filename)
            raise


    @property
    def stat(self):
        try:
            return os.stat(self.filename)
        except OSError:
            return (0,)*10

    @cached_property
    def mimetype(self):
        typ, encoding = mimetypes.guess_type(self.filename)
        if typ is None:
            mimetype = ('', '')
        else:
            mimetype = tuple(typ.split('/'))
        return mimetype

    @property
    def filesize(self):
        return self.stat[stat.ST_SIZE]

    def __repr__(self):
        if self.filename is None:
            return '<New Document %d>'%self.newfile_index
        else:
            return '<Document %r>'%self.filename

    @property
    def modified_time(self):
        return self.stat[stat.ST_MTIME]

    @property
    def encoding(self):
        self._load()
        return self._encoding

    @property
    def lines(self):
        self._load()
        return self._lines

    @property
    def content(self):
        self._load()
        return self._str

    @property
    def directory(self):
        return os.path.dirname(self.filename)

    @property
    def directory_basename(self):
        return os.path.basename(self.directory)

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @property
    def directory_colour(self):
        return self.markup_directory_color


    @property
    def unique_id(self):
        #XXX: this is kinda obsolete
        #     the creation_time attribute does the same thing
        return self.creation_time

    @property
    def markup(self):
        prefix = '<b><tt>%s </tt></b>' % self.markup_prefix
        if self.filename is not None:
            s = self.markup_string % self._build_markup_dict()
        else:
            s = '<b>New File %s</b>' % self.newfile_index
        return '%s%s' % (prefix, s)

    def _build_markup_dict(self):
        markup_dict = {}
        for attr in self.markup_attributes:
            markup_dict[attr] = getattr(self, attr)
        return markup_dict

    @property
    def handler(self):
        return self._handler

    @property
    def project_name(self):
        if self.project is not None:
            return self.project.get_display_name()
        else:
            return ''

    def get_project_relative_path(self):
        if self.filename is None:
            return None, None

        #XXX: 
        match = self.boss.cmd('project', 'get_project_for_document', document=self)
        if match is None:
            return None, os.path.join(os.path.split(self.directory)[-2:])
        else:
            project, path = match
            return project, path


    @property
    def is_new(self):
        return self.filename is None
