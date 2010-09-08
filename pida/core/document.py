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
import itertools

import codecs

from pida.core.log import log
from pida.utils.descriptors import cached_property

from xml.sax.saxutils import escape

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext

new_file_counter = itertools.count(1)

class Document(object):
    """
    Represents a document.

    A document can eighter be just a file. Or be opened by the editor component
    and is then a live document (live is True).

    """

    usage = 0
    last_opened = 0

    editor_buffer_id = None

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
            self.newfile_index = None
        else:
            self.filename = None
            self.newfile_index = next(new_file_counter)

        self.editor = None
        self.creation_time = time.time()
        self._project = project



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
            return u'<New Document {self.newfile_index}>'.format(self=self)
        else:
            return u'<Document {self.filename!r}>'.format(self=self)

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
    def modified_time(self):
        if self.filename:
            return self.stat[stat.ST_MTIME]
        return self.creation_time

    @property
    def content(self):
        """
        the content of the document.
        tries buffer content, falls back to file conten
        """
        if hasattr(self.editor, 'get_content'):
            return self.boss.editor.get_content(self.editor)
        with open(self.filename) as fp:
            return fp.read()


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
    def unique_id(self):
        return id(self)

    @property
    def project_name(self):
        """
        Name of Project or None
        """
        return getattr(self.project, 'display_name', '')

    @property
    def is_new(self):
        """
        True if the Document is not associated to a filename
        """
        return self.filename is None

    def __nonzero__(self):
        # documents are always True
        return True


class DocumentException(Exception):
    """Raised when the file can't be loaded by a editor"""
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        self.orig = kwargs.pop('orig', None)
        super(DocumentException, self).__init__(*args, **kwargs)

