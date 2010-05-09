# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    pida.core.document
    ~~~~~~~~~~~~~~~~~~

    :license: GPL2 or later
    :copyright: 2005-2008 by The PIDA Project

"""
import os
import mimetypes
mimetypes.init() # expensive shit to keep mimetypes.guess_type threadsave
import stat
import time

from charfinder import detect_encoding
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
    and is then a live document (live is True).

    A document can be accessed like a List object (list of lines). Each line
    however does have its tailing newline character as it's supposed not
    to alter data.

    """

    markup_prefix = ''
    markup_directory_color = '#FFFF00'
    markup_project_color = '#FF0000'
    markup_color_noproject = "#FF0000"

    markup_attributes = ['project_name', 'project_relative_path', 'basename',
                         'markup_project_color', 'markup_directory_color',
                         'filename', 'directory', 'markup_color_noproject']

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

    markup_string_tworow = (
                     u'<b>%(basename)s</b>\n'
                     u'<small>%(markup_inc)s</small>')

    markup_string_tworow_project = (
                     u'<span foreground="%(markup_project_color)s">'
                     u'%(project_name)s</span><tt>:</tt>'
                     u'<span foreground="%(markup_directory_color)s">'
                     u'%(project_relative_path)s/</span>'
                     u'%(basename)s')

    markup_string_tworow_fullpath = (
                     u'<span foreground="%(markup_directory_color)s">'
                     u'%(directory)s/</span>'
                     u'%(basename)s')

    markup_string_noproject_file = (
                     u'<span foreground="%(markup_color_noproject)s">'
                     u'<b>%(basename)s</b></span>'
                     )

    markup_string = u'<b>%(basename)s</b>'

    usage = 0
    last_opened = 0

    editor_buffer_id = None

    @property
    def markup_string_if_project(self):
        if not self.project:
            return self.markup_string_noproject_file
        return self.markup_string

    def __init__(self, boss, filename=None, project=None):
        """
        Create a new Document instance.

        @boss: boss this document belongs to
        @filename: path to the file or None (unamed buffer)
        @project: project this document belongs to
        """
        self.boss = boss
        if filename is not None:
            self.filename = os.path.realpath(filename)
        else:
            self.filename = None
        self.editor = None
        self._list = []
        self._str = ""
        self.creation_time = time.time()
        self._project = project

        if filename is None:
            global new_file_index
            self.newfile_index = new_file_index
            new_file_index = new_file_index + 1
        else:
            self.newfile_index = None

        self.clear()


    def project_and_path(self):
        if self.filename is None:
            return None, None
        if self.boss is not None:
            return self.boss.cmd('project', 'get_project_for_document', document=self)

    @property
    def project(self):
        if self._project is not None:
            return self._project
        pp = self.project_and_path()
        if pp is not None:
            self._project = pp[0]
            return pp[0]

    @property
    def project_relative_path(self):
        pp = self.project_and_path()
        if pp is not None:
            return pp[1]
        return os.path.join(*os.path.split(self.directory)[-2:])


    def clear(self):
        """
        Clear document caches
        """
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

            self._encoding = detect_encoding(stream, fname, mime)
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


    def _get_doctype(self):
        #FIXME: need a interface to pull doctype from the editor if
        # we are live
        if hasattr(self, '_doctype'):
            return self._doctype
        elif self.boss is not None:
            lmn = self.boss.get_service('language')
            if not lmn:
                return None
            self._doctype = lmn.doctypes.guess_doctype_for_document(self)

            return self._doctype

        return None

    def _set_doctype(self, doctype):
        #FIXME: we need a interface setting the editors language here
        self._doctype = doctype

    doctype = property(_get_doctype, _set_doctype)

    @property
    def stat(self):
        """
        Returns the stat of the current file
        """
        try:
            return os.stat(self.filename)
        except (OSError, TypeError):
            return (0,) * 10

    @cached_property
    def mimetype(self):
        """
        Returns the mimetype guessed from the file
        """
        #FIXME: use doctypes
        typ, encoding = mimetypes.guess_type(self.filename)
        if typ is None:
            mimetype = ('', '')
        else:
            mimetype = tuple(typ.split('/'))
        return mimetype

    @property
    def filesize(self):
        """
        Filesize of Document
        """
        return self.stat[stat.ST_SIZE]

    def __repr__(self):
        if self.filename is None:
            return u'<New Document %d (%s)>' % (self.newfile_index, self.unique_id)
        else:
            return u'<Document %r (%s)>' % (self.filename, self.unique_id)

    def __unicode__(self):
        if self.filename is None:
            if self.newfile_index > 1:
                return _(u'Untitled (%d)') % (self.newfile_index)
            return _(u'Untitled')
        else:
            if self.project:
                return u'%s:%s/%s' % (self.project_name,
                                      self.project_relative_path, self.basename)
            else:
                return os.path.basename(self.filename)

    @property
    def markup_title(self):
        """
        Returns a markup version of unicode
        """
        if self.filename is None:
            if self.newfile_index > 1:
                return _(u'<b>Untitled (%d)</b>') % (self.newfile_index)
            return _(u'<b>Untitled</b>')
        else:
            if self.project:
                return u'%s:%s/<b>%s</b>' % (
                        escape(self.project_name),
                        escape(self.project_relative_path),
                        escape(self.basename))
            else:
                return '<b>%s</b>' % escape(os.path.basename(self.filename))

    @property
    def modified_time(self):
        if self.filename:
            return self.stat[stat.ST_MTIME]
        return self.creation_time

    @property
    def encoding(self):
        """
        Encoding of file
        """
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
    def live(self):
        """
        Returns a boolean if the document is loaded in the editor
        """
        # live indicates that this object has a editor instance which get_content
        #self.live = False
        if self.editor and hasattr(self.editor, 'get_content'):
            return True

        return False

    def get_content(self, live=True):
        """
        Returns the content of the document.
        If live is true and the document is loaded into an editor the
        content of the editor is returned
        """
        if live and hasattr(self.editor, 'get_content'):
            return self.boss.editor.get_content(self.editor)
        self._load()
        return self._str

    def set_content(self, value, flush=True, live=True):
        """
        Sets the content of the document.
        If live is True and the document is loaded, it's content is returned
        """
        if self.boss is not None and hasattr(self.boss.editor, 'set_content') and self.editor:
            return self.boss.editor.set_content(self.editor, value)

        self._str = value
        self._lines = self._str.splitlines(True)

        if flush:
            self.flush()

    content = property(get_content, set_content)

    def flush(self):
        """
        Flush the buffer.
        If editor has loaded this document, it's value
        is fetched befor writing to disc
        """
        if self.boss is not None and hasattr(self.editor, 'get_content') and self.editor:
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
            return self.boss.editor.set_content(self.editor, self._str)
        self.set_content(self._str, flush=False)

    @property
    def directory(self):
        """
        Directory name the Document is located in
        """
        if self.is_new:
            return None
        return os.path.dirname(self.filename)

    @property
    def directory_basename(self):
        """
        Directory's name the Document is located in
        """
        if self.is_new:
            return None
        return os.path.basename(self.directory)

    @property
    def basename(self):
        """
        Basename of the file. It's actuall filename
        """
        if self.is_new:
            return None
        return os.path.basename(self.filename)

    @property
    def directory_colour(self):
        return self.markup_directory_color

    @property
    def unique_id(self):
        return id(self)

    def get_markup(self, markup_string=None, style=None):
        """
        Returns a markup version the Document designed for
        beeing embedded in gtk views
        """
        if markup_string is None:
            if self.project:
                markup_string = self.markup_string_project
            else:
                markup_string = self.markup_string

        prefix = u'<b><tt>%s </tt></b>' % self.markup_prefix
        if self.filename is not None:
            s = markup_string % self._build_markup_dict(style=style)
        else:
            s = u'<b>%s</b>' % escape(self.__unicode__())
        return '%s%s' % (prefix, s)

    markup = property(get_markup)

    def get_markup_tworow(self, style=None):
        """
        Two rowed version of above
        """
        if self.project:
            mark = self.get_markup(self.markup_string_tworow_project)
        else:
            mark = self.get_markup(self.markup_string_tworow_fullpath)
        rv = self.markup_string_tworow % self._build_markup_dict(markup_dict={
            'markup_inc': mark
            }, style=style)
        return rv

    markup_tworow = property(get_markup_tworow)

    def _build_markup_dict(self, markup_dict=None, style=None):
        if not markup_dict:
            markup_dict = {}
        for attr in self.markup_attributes:
            var = getattr(self, attr)
            if var:
                markup_dict[attr] = escape(var)
            else:
                markup_dict[attr] = ''

        return markup_dict

    @property
    def project_name(self):
        """
        Name of Project or None
        """
        if self.project is not None:
            return self.project.display_name
        else:
            return ''

    @property
    def is_new(self):
        """
        True if the Document is not associated to a filename
        """
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
        """
        Add a line to the Document
        """
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

