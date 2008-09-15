# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.document
    ~~~~~~~~~~~~~~~~~~

    :license: GPL3 or later
    :copyright:
        * 2005 Ali Afshar
        * 2008 Ronny Pfannschmidt
"""
import os
import mimetypes
import stat
import time

from charfinder import DETECTOR_MANAGER
import codecs

from pida.core.log import log
from pida.utils.descriptors import cached_property

from xml.sax.saxutils import escape

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


new_file_index = 1

class Document(object):
    """Represents a file on disk."""

    markup_prefix = ''
    markup_directory_color = '#0000c0'
    markup_project_color = '#600060'
    markup_attributes = ['project_name', 'project_relative_path', 'basename',
                         'markup_project_color', 'markup_directory_color', 
                         'filename', 'directory']
    markup_string_project = (
                     u'<span color="%(markup_project_color)s">'
                     u'%(project_name)s</span><tt>:</tt>'
                     u'<span color="%(markup_directory_color)s">'
                     u'%(project_relative_path)s/</span>'
                     u'<b>%(basename)s</b>')

    markup_string_fullpath = (
                     u'<span color="%(markup_directory_color)s">'
                     u'%(directory)s/</span>'
                     u'<b>%(basename)s</b>')

    markup_string = (u'<b>%(basename)s</b>')


    def __init__(self, boss, filename=None, project=None):
        self.boss = boss
        self.filename = filename
        self.project = project
        self._detect_encoding = DETECTOR_MANAGER
        self.creation_time = time.time()

        if filename is None:
            global new_file_index
            self.newfile_index = new_file_index
            new_file_index = new_file_index + 1
        else:
            self.newfile_index = None
            
        if project is None:
            self.project, self.project_relative_path = self.get_project_relative_path()
        else:
            self.project_relative_path = project.get_relative_path_for(filename)

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
        except IOError:
            if stream is not None:
                stream.close()

            # set the encoding to None and the rest too empty
            self.clear()
            self._str = ''
            self._lines = []
            self._encoding = 'none'

            log.warn(_('failed to open file %s'), self.filename)


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
            return u'<New Document %d (%s)>' %(self.newfile_index, self.unique_id)
        else:
            return u'<Document %r (%s)>' %(self.filename, self.unique_id)

    def __unicode__(self):
        if self.filename is None:
            if self.newfile_index > 1:
                return _(u'Untitled (%d)') %(self.newfile_index)
            return _(u'Untitled')
        else:
            if self.project:
                return u'%s:%s/%s' %(self.project_name,
                                     self.project_relative_path, self.basename)
            else:
                return os.path.basename(self.filename)
        
    @property
    def markup_title(self):
        """Returns a markup version of unicode"""
        if self.filename is None:
            if self.newfile_index > 1:
                return _(u'<b>Untitled (%d)</b>') %(self.newfile_index)
            return _(u'<b>Untitled</b>')
        else:
            if self.project:
                return u'%s:%s/<b>%s</b>' %(escape(self.project_name),
                                     escape(self.project_relative_path), 
                                     escape(self.basename))
            else:
                return '<b>%s</b>' %escape(os.path.basename(self.filename))
        
    @property
    def modified_time(self):
        return self.stat[stat.ST_MTIME]

    @property
    def encoding(self):
        self._load()
        # FIXME: if self.is_new we should run the _encode detection from
        # the editors buffer if possible
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
        if self.is_new:
            return None
        return os.path.dirname(self.filename)

    @property
    def directory_basename(self):
        if self.is_new:
            return None
        return os.path.basename(self.directory)

    @property
    def basename(self):
        if self.is_new:
            return None
        return os.path.basename(self.filename)

    @property
    def directory_colour(self):
        return self.markup_directory_color

    @property
    def unique_id(self):
        return id(self)

    def get_markup(self, markup_string=None):
        if markup_string is None:
            if self.project:
                markup_string = self.markup_string_project
            else:
                markup_string = self.markup_string
        prefix = u'<b><tt>%s </tt></b>' % self.markup_prefix
        if self.filename is not None:
            s = markup_string % self._build_markup_dict()
        else:
            s = u'<b>%s</b>' % escape(self.__unicode__())
        return '%s%s' % (prefix, s)

    markup = property(get_markup)

    def _build_markup_dict(self):
        markup_dict = {}
        for attr in self.markup_attributes:
            markup_dict[attr] = escape(getattr(self, attr))
        return markup_dict

    @property
    def project_name(self):
        if self.project is not None:
            return self.project.display_name
        else:
            return ''

    def get_project_relative_path(self):
        if self.filename is None:
            return None, None

        #XXX: move to buffer manager
        match = self.boss.cmd('project', 'get_project_for_document', document=self)
        if match is None:
            return None, os.path.join(*os.path.split(self.directory)[-2:])
        else:
            project, path = match
            return project, path


    @property
    def is_new(self):
        return self.filename is None


class DocumentException(Exception):
    """Raised when the file can't be loaded by a editor"""
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        self.orig = kwargs.pop('orig', None)
        super(DocumentException, self).__init__(*args, **kwargs)

