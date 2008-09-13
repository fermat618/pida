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
    """
    Represents a document.
    
    A document can eighter be just a file. Or be opened by the editor component
    and is then a life document (life is True).

    A document can be accessed like a List object (list of lines). Each line
    however does have its tailing newline character as it's supposed not
    to alter data.

    
    """

    markup_prefix = ''
    markup_directory_color = '#0000c0'
    markup_attributes = ['project_name', 'project_relative_path', 'basename',
                         'directory_colour']
    markup_string = (u'<span color="#600060">'
                     u'%(project_name)s</span><tt>:</tt>'
                     u'<span color="%(directory_colour)s">'
                     u'%(project_relative_path)s/</span>'
                     u'<b>%(basename)s</b>')

    def __init__(self, boss, filename=None, project=None):
        self.boss = boss
        self.filename = filename
        self.project = project
        self.editor = None
        self._list = []
        self._str = ""
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
            self._lines = self._str.splitlines(True)
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
        #FIXME: use doctypes
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
        import warnings
        warnings.warn("Deprecated. Access the document as a list")
        self._load()
        return self._lines

    @property
    def life(self):
        # life indicates that this object has a editor instance which get_content
        #self.life = False
        if self.editor and hasattr(self.editor, 'get_content'):
            return True

        return False

    def get_content(self):
        if hasattr(self.editor, 'get_content') and self.editor:
            return self.boss.editor.get_content(self.editor)
        self._load()
        return self._str

    def set_content(self, value, flush=True):
        if hasattr(self.boss.editor, 'set_content') and self.editor:
            return self.boss.editor.set_content(self.editor, value)

        self._str = value
        self._lines = self._str.splitlines(True)
        
        if flush:
            self.flush()

    content = property(get_content, set_content)

    def flush(self):
        if hasattr(self.editor, 'get_content') and self.editor:
            value = self.boss.editor.get_content(self.editor)
        else:
            value = self._str

        stream = None
        try:
            stream = open(self.filename, "wb")
            stream.write(value)
            stream.close()
            # update the _last_mtime var, so the next access
            # will not cause a file read
            self._last_mtime = self.modified_time
        except IOError:
            if stream is not None:
                stream.close()
        
    def _update_content_from_lines(self):
        self._str = "".join(self._lines)
        if hasattr(self.boss.editor, 'set_content') and self.editor:
            return self.boss.editor.set_content(self.editor, value)
        self.set_content(self._str, flush=False)
        
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

    @property
    def markup(self):
        prefix = u'<b><tt>%s </tt></b>' % self.markup_prefix
        if self.filename is not None and self.project:
            s = self.markup_string % self._build_markup_dict()
        else:
            s = u'<b>%s</b>' % escape(self.__unicode__())
        return '%s%s' % (prefix, s)

    def _build_markup_dict(self):
        markup_dict = {}
        for attr in self.markup_attributes:
            markup_dict[attr] = getattr(self, escape(attr))
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

    # emulate a container element. this allows access to a document
    # as a list of lines
    def __len__(self):
        return len(self._list)
        
    def __getitem__(self, key):
        return self._list[key]
        
    def __setitem__(self, key, value):
        self._list[key] = value
        self._update_content_from_lines()

    def __delitem__(self, key):
        del self._list[key]
        self._update_content_from_lines()

    def __iter__(self):
        return iter(self._list)
        
    def append(self, line):
        self._list.append(line)
        self._update_content_from_lines()
        
    def __nonzero__(self):
        # documents are always True
        return True


class DocumentException(Exception):
    """Raised when the file can't be loaded by a editor"""
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        self.orig = kwargs.pop('orig', None)
        super(DocumentException, self).__init__(*args, **kwargs)

