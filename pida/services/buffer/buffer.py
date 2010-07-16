# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os

import gtk
import time


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.options import OptionsConfig, choices
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.pdbus import DbusConfig, EXPORT

from pida.ui.views import WindowConfig
from pida.core.document import Document, DocumentException

from pygtkhelpers.gthreads import gcall

# locale
from pida.core.locale import Locale
locale = Locale('buffer')
_ = locale.gettext

from .view import BufferListView, attributes

LEXPORT = EXPORT(suffix='buffer')



class BufferActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'open_file',
            gtk.Action,
            _('_Open File'),
            _('Open a file with a graphical file browser'),
            gtk.STOCK_OPEN,
            self.on_open_file,
            '<Shift><Control>O',
        )

        self.create_action(
            'open-for-file',
            gtk.Action,
            _('Open File'),
            _('Open this file'),
            gtk.STOCK_OPEN,
            self.on_open_for_file,
        )

        self.create_action(
            'new_file',
            gtk.Action,
            _('_New File'),
            _('Create a new file'),
            gtk.STOCK_NEW,
            self.on_new_file,
            '<Shift><Control>N',
        )

        self.create_action(
            'create_file',
            gtk.Action,
            _('Cr_eate File'),
            _('Create a new file'),
            gtk.STOCK_ADD,
            self.on_add_file,
            '<Shift><Control>A',
        )

        self.create_action(
            'close',
            gtk.Action,
            _('_Close Document'),
            _('Close the current document'),
            gtk.STOCK_CLOSE,
            self.on_close,
            '<Shift><Control>W',
        )

        self.create_action(
            'close_all',
            gtk.Action,
            _('Close all Documents'),
            _('Close all documents'),
            '',
            self.on_close_all,
            '',
        )
        self.create_action(
            'switch_next_buffer',
            gtk.Action,
            _('_Next Buffer'),
            _('Switch to the next buffer'),
            gtk.STOCK_GO_DOWN,
            self.on_next_buffer,
            '<Alt>Down',
        )

        self.create_action(
            'switch_prev_buffer',
            gtk.Action,
            _('_Previous Buffer'),
            _('Switch to the previous buffer'),
            gtk.STOCK_GO_UP,
            self.on_prev_buffer,
            '<Alt>Up',
        )
        self.create_action(
            'show_buffer_list',
            gtk.Action,
            _('Show _buffer browser'),
            _('Displays the buffer window'),
            '',
            self.on_show_buffer,
            '<Shift><Control>b',
            global_=True
        )

        self.create_action(
            'close_selected',
            gtk.Action,
            _('_Close Document'),
            _('Close the selected document'),
            gtk.STOCK_CLOSE,
            self.on_close_selected,
        )

    def on_open_file(self, action):
        project = self.svc.boss.cmd('project', 'get_current_project')
        if project:
            current_folder = project.source_directory
        else:
            current_folder = None 
        file_name = self.svc.boss.window.open_dlg(folder=current_folder)
        if file_name:
            self.svc.open_file(file_name)

    def on_new_file(self, action):
        self.svc.new_file()

    def on_add_file(self, action):
        current_folder = self.svc.boss.cmd('filemanager', 'get_browsed_path')
        file_name = self.svc.boss.window.save_dlg(folder=current_folder)
        if file_name:
            f = open(file_name, 'w')
            f.close()
            self.svc.open_file(file_name)

    def on_close(self, action):
        self.svc.close_current()

    def on_close_all(self, action):
        self.svc.close_all()

    def on_open_for_file(self, action):
        file_name = action.contexts_kw['file_name']
        self.svc.open_file(file_name)

    def on_next_buffer(self, action):
        self.svc.get_view().next_buffer()

    def on_prev_buffer(self, action):
        self.svc.get_view().prev_buffer()

    def on_show_buffer(self, action):
        self.svc.cmd('present_view')

    def on_close_selected(self, action):
        document = action.contexts_kw.get('document')
        self.svc.close_file(document=document)

class BufferListConfig(WindowConfig):
    key = BufferListView.key
    label_text = BufferListView.label_text
    description = "Buffer List"

class BufferFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc, 'buffer-file-menu.xml'))
        self.subscribe_foreign('window', 'window-config',
            BufferListConfig)

class BufferEventsConfig(EventsConfig):

    def create(self):
        self.publish('document-saved', 'document-changed', 
            'document-typchanged', 'document-closed', 'document-opened', 
            'document-goto')
        self.subscribe('document-saved', self.on_document_change)
        self.subscribe('document-changed', self.on_document_change)
        self.subscribe('document-typchanged', self.on_document_change)

    def subscribe_all_foreign(self):
        self.subscribe_foreign('editor', 'started', self.on_editor_started)

    def on_editor_started(self, *k, **kw):
        print 'editor started'

        try:
            #XXX: will mess wuth the signaling doe opening files
            #     will create inconsistent state while the default impl is
            #     working
            files = self.svc.opt('open_files')
            print 'opening', files
            self.svc.open_files(files)
        except Exception as e:
            self.svc.log.exception(e)

    def on_document_change(self, *args, **kwargs):
        # we have to update the document buffer when one doc changes as
        # the list should be sorted all the time
        self.svc.get_view().sort()

class BufferOptionsConfig(OptionsConfig):
    def create_options(self):
        self.create_option(
            'display_type',
            _('Display notebook title'),
            choices({'onerow':_('One Row'), 
                     'tworow':_('Filename and Path seperate ')}),
            'tworow',
            _('Type to display in the Buffer window'),
            self.on_display_type_change
        )
        self.create_option(
            'open_files',
            'the currently open files',
            list,
            [],
            ''
            )

    def on_display_type_change(self, option):
        self.svc.get_view().set_display_attr(attributes[option.value])


class BufferCommandsConfig(CommandsConfig):

    def new_file(self, do_open=True, with_editor_id=None):
        self.svc.new_file(do_open, with_editor_id)

    def open_file(self, file_name=None, document=None, line=None, offset=None,
                  editor_buffer_id=None, do_open=True):
        #if not file_name and not document and not editor_buffer_id:
        #    return
        self.svc.open_file(file_name, document, line=line, offset=offset,
                           editor_buffer_id=editor_buffer_id, do_open=do_open)

    def open_files(self, files):
        self.svc.open_files(files)

    def close_file(self, file_name=None, document=None,
                   editor_buffer_id=None):
        #if not file_name and not document:
        #    return
        self.svc.close_file(file_name=file_name, document=document,
                            editor_buffer_id=editor_buffer_id)

    def close_all(self):
        self.svc.close_all()

    def current_file_saved(self):
        self.svc.file_saved()

    def get_view(self):
        return self.svc.get_view()

    def get_current(self):
        return self.svc.get_current()

    def get_documents(self):
        return self.svc.get_documents()

    def get_buffer_names(self):
        return [x.filename for x in self.get_documents().itervalues()]

    def present_view(self):
        view = self.svc.get_view()
        return self.svc.boss.cmd('window', 'present_view',
            view=view)
        view.buffers_ol.grab_focus()

    def get_document_by_id(self, document_id=None):
        if document_id:
            return self.svc._documents.get(document_id, None)

class BufferDbusConfig(DbusConfig):

    @LEXPORT(in_signature='s')
    def open_file(self, file_name):
        self.svc.open_file(file_name)

    @LEXPORT(in_signature='as')
    def open_files(self, files):
        self.svc.open_files(files)
        
    @LEXPORT(in_signature='s')
    def close_file(self, file_name):
        self.svc.close_file(file_name)
        
    @LEXPORT(out_signature='i')
    def get_open_documents_count(self):
        return len(self.svc._documents)

    @LEXPORT(out_signature='a(isiia{ss})')
    def get_documents(self):
        return [
                 (id(x), x.filename, 
                       x.doctype and x.doctype.internal or '', 
                       x.creation_time,
                       # extended values
                       {})
                  for x in self.svc._documents.itervalues()
               ]


# Service class
class Buffer(Service):
    """
    Buffer is a graphical manager for editor buffers.
    """ 

    commands_config = BufferCommandsConfig
    actions_config = BufferActionsConfig
    events_config = BufferEventsConfig
    features_config = BufferFeaturesConfig
    dbus_config = BufferDbusConfig
    options_config = BufferOptionsConfig

    def pre_start(self):
        self._documents = {}
        self._current = None
        #XXX hideous hack for vim
        self._last_added_document = None
        self._view = BufferListView(self)
        self.get_action('close').set_sensitive(False)
        self._refresh_buffer_action_sensitivities()

    def pre_stop(self):
        self.set_opt('open_files', [
            d.filename for d in self._documents.itervalues()
            if d.filename is not None
            ])
        return True

    def get_view(self):
        return self._view

    def _refresh_buffer_action_sensitivities(self):
        for action_name in ['switch_next_buffer', 'switch_prev_buffer']:
            self.get_action(action_name).set_sensitive(bool(self._documents))

    def new_file(self, do_open=True, with_editor_id=None):
        return self.open_file(editor_buffer_id=with_editor_id)

    def open_file(self, file_name=None, document=None, line=None, offset=None,
                  editor_buffer_id=None, do_open=True):
        if file_name:
            file_name = os.path.realpath(file_name)
        if document is None:
            # try to find the document
            if editor_buffer_id is not None:
                document = self._get_document_for_editor_id(editor_buffer_id)
            if document is None and file_name is not None:
                document = self._get_document_for_filename(file_name)
            elif file_name is None and editor_buffer_id is not None:
                #XXX new file just switched, can't know, have to guess!
                # normally fall back to filename
                if self._last_added_document and self._last_added_document.is_new:
                    document = self._last_added_document
                    self._last_added_document = None
            # can't find it
            if document is None:
                document = Document(self.boss, file_name)
                if editor_buffer_id is not None:
                    document.editor_buffer_id = editor_buffer_id
                self._add_document(document)
        self.view_document(document, line=line, offset=offset, do_open=do_open)
        self.emit('document-opened', document=document)
        return document


    def open_files(self, files):
        if not files:
            # empty list
            return
        docs = []
        for file_name in files:
            document = Document(self.boss, file_name)
            self._add_document(document)
            docs.append(document)
        self.boss.editor.cmd('open_list', documents=docs)
        for document in docs:
            self.emit('document-opened', document=document)

    def recover_loading_error(self, error):
        # recover from a loading exception
        if error.document:
            filename = error.document.filename
        else:
            filename = ""
        self.notify_user(error.message, title=_("Can't load file %s") % filename )
        self.log.warning('error loading file(s): %s' %error.message)
        if error.document:
            self._remove_document(error.document)
        # switch to the first doc to make sure editor gets consistent
        if self._documents:
            self.view_document(self._documents[self._documents.keys()[0]])
        #self.log.exception(err)

    def close_current(self):
        document = self._current
        if document is not None:
            if self.boss.editor.cmd('close', document=document):
                self._remove_document(document)
                self.emit('document-closed', document=document)

    def close_file(self, file_name = None, document = None,
                   editor_buffer_id=None):

        if not document:
            if editor_buffer_id is not None:
                document = self._get_document_for_editor_id(editor_buffer_id)
            if not document and file_name is not None:
                document = self._get_document_for_filename(file_name)
        if document is not None:
            if editor_buffer_id is not None:
                self._remove_document(document)
                self.emit('document-closed', document=document)
            else:
                if self.boss.editor.cmd('close', document=document):
                    self._remove_document(document)
                    self.emit('document-closed', document=document)

    def close_all(self):
        docs = self._documents.values()[:]
        for document in docs:
            if self.boss.editor.cmd('close', document=document):
                self._remove_document(document)
                self.emit('document-closed', document=document)
            else:
                break

    def _get_document_for_filename(self, file_name):
        for uid, doc in self._documents.iteritems():
            if doc.filename == file_name:
                return doc

    def _get_document_for_editor_id(self, bufid):
        for uid, doc in self._documents.iteritems():
            if doc.editor_buffer_id == bufid:
                return doc


    def _add_document(self, document):
        self._last_added_document = document
        self._documents[id(document)] = document
        self._view.add_document(document)
        self._refresh_buffer_action_sensitivities()

    def _remove_document(self, document):
        "_remove_doc", document
        del self._documents[id(document)]
        self._view.remove_document(document)
        self._refresh_buffer_action_sensitivities()

    def view_document(self, document, line=None, offset=None, do_open=True):
        self._view.buffers_ol.update(document)
        if document is not None and self._current != document:
            self._current = document
            self._current.usage += 1
            self._current.last_opend = time.time()
            self._view.set_document(document)
            try:
                if do_open:
                    self.boss.editor.cmd('open', document=document)
            except DocumentException, e:
                # document can't be loaded. we have to remove the document from 
                # the system
                self.recover_loading_error(e)
                return
            self.emit('document-changed', document=document)
        if offset is not None:
            if line is not None:
                raise ValueError('Cannot pass offset and line')
            else:
                gcall(self.boss.editor.set_cursor_position, offset)
        elif line is not None:
            gcall(self.boss.editor.goto_line, line)
        self.get_action('close').set_sensitive(document is not None)

    def file_saved(self):
        self.emit('document-saved', document=self._current)

    def get_current(self):
        return self._current

    def get_documents(self):
        return self._documents


# Required Service attribute for service loading
Service = Buffer



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
