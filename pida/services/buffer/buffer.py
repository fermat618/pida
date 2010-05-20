# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os
from tempfile import mkstemp

import gtk
import time

from pygtkhelpers.ui.objectlist import Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.options import OptionsConfig, choices
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView, WindowConfig
from pida.ui.objectlist import AttrSortCombo
from pida.core.document import Document, DocumentException

from pida.utils.gthreads import gcall

# locale
from pida.core.locale import Locale
locale = Locale('buffer')
_ = locale.gettext

LEXPORT = EXPORT(suffix='buffer')

attributes = {
    'onerow': 'markup',
    'tworow': 'markup_tworow',
}

class BufferListView(PidaGladeView):

    key = 'buffer.list'
    gladefile = 'buffer_list'
    locale = locale
    icon_name = 'package_office'

    label_text = _('Buffers')

    def create_ui(self ):
        self.buffers_ol.set_columns([
            Column('markup', use_markup=True),
            Column('markup_tworow', use_markup=True, visible=False),
            Column("basename", visible=False, searchable=True),
        ])

        self.buffers_ol.set_headers_visible(False)
        self._sort_combo = AttrSortCombo(self.buffers_ol,
            [
                ('creation_time', _('Time Opened')),
                ('filename', _('File path')),
                ('basename', _('File name')),
                ('mimetype', _('Mime Type')),
                ('doctype', _('Document Type')),
                ('length', _('File Length')),
                ('modified_time', _('Last Modified')),
                ('usage', _('View Counter')),
                ('last_opend', _('Last Opened')),
                #('Project', _('Project_name'))
            ],
            'creation_time' 
        )
        self._sort_combo.show()
        self.toplevel.pack_start(self._sort_combo, expand=False)

    def add_document(self, document):
        self.buffers_ol.append(document)

    def remove_document(self, document):
        self.buffers_ol.remove(document)

    def set_document(self, document):
        if self.buffers_ol.selected_item is not document:
            self.buffers_ol.selected_item = document

    def view_document(self, document):
        self.svc.view_document(document)
        self.svc.boss.editor.cmd('grab_focus')

    def on_buffers_ol__item_double_clicked(self, ol, item, ev=None):
        self.view_document(item)

    def on_buffers_ol__item_activated(self, ol, item):
        self.view_document(item)

    def on_buffers_ol__item_right_clicked(self, ol, item, event=None):
        menu = self.svc.boss.cmd('contexts', 'get_menu', context='file-menu',
                                 document=item, file_name=item.filename)

        # Add some stuff to the menu
        close = self.svc.get_action('close_selected').create_menu_item()
        menu.insert(close, 2)

        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

        # Must leave the menu in the same state we found it!
        def on_deactivate(menu):
            #menu.remove(sep)
            menu.remove(close)

        menu.connect('deactivate', on_deactivate)

    def get_current_buffer_index(self):
        return self.buffers_ol.selected_item

    def select_buffer_by_index(self, index):
        self.buffers_ol.select(self.buffers_ol[index])
        self.view_document(self.buffers_ol[index])

    # note current is the current buffer, not the current selected buffer
    def next_buffer(self):
        next = self.buffers_ol.item_after(self.svc.get_current())
        if next is None:
            next = self.buffers_ol[0]
        self.svc.open_file(document=next)

    def prev_buffer(self):
        prev = self.buffers_ol.item_before(self.svc.get_current())
        if prev is None:
            prev = self.buffers_ol[-1]
        self.svc.open_file(document=prev)

    def sort(self):
        self.buffers_ol.get_model().sort_column_changed()

    def set_display_attr(self, newattr):
        for attr in attributes.values():
            for col in self.buffers_ol._viewcols_for_attr(attr):
                col.props.visible = attr==newattr


class BufferActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'open_file',
            TYPE_NORMAL,
            _('_Open File'),
            _('Open a file with a graphical file browser'),
            gtk.STOCK_OPEN,
            self.on_open_file,
            '<Shift><Control>O',
        )

        self.create_action(
            'open-for-file',
            TYPE_NORMAL,
            _('Open File'),
            _('Open this file'),
            gtk.STOCK_OPEN,
            self.on_open_for_file,
        )

        self.create_action(
            'new_file',
            TYPE_NORMAL,
            _('_New File'),
            _('Create a new file'),
            gtk.STOCK_NEW,
            self.on_new_file,
            '<Shift><Control>N',
        )

        self.create_action(
            'create_file',
            TYPE_NORMAL,
            _('Cr_eate File'),
            _('Create a new file'),
            gtk.STOCK_ADD,
            self.on_add_file,
            '<Shift><Control>A',
        )

        self.create_action(
            'close',
            TYPE_NORMAL,
            _('_Close Document'),
            _('Close the current document'),
            gtk.STOCK_CLOSE,
            self.on_close,
            '<Shift><Control>W',
        )

        self.create_action(
            'close_all',
            TYPE_NORMAL,
            _('Close all Documents'),
            _('Close all documents'),
            '',
            self.on_close_all,
            '',
        )
        self.create_action(
            'switch_next_buffer',
            TYPE_NORMAL,
            _('_Next Buffer'),
            _('Switch to the next buffer'),
            gtk.STOCK_GO_DOWN,
            self.on_next_buffer,
            '<Alt>Down',
        )

        self.create_action(
            'switch_prev_buffer',
            TYPE_NORMAL,
            _('_Previous Buffer'),
            _('Switch to the previous buffer'),
            gtk.STOCK_GO_UP,
            self.on_prev_buffer,
            '<Alt>Up',
        )
        self.create_action(
            'show_buffer_list',
            TYPE_NORMAL,
            _('Show _buffer browser'),
            _('Displays the buffer window'),
            '',
            self.on_show_buffer,
            '<Shift><Control>b',
            global_=True
        )

        self.create_action(
            'close_selected',
            TYPE_NORMAL,
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
                 (x.unique_id, x.filename, 
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
            self.get_action(action_name).set_sensitive(len(self._documents) > 0)

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
        self._documents[document.unique_id] = document
        self._view.add_document(document)
        self._refresh_buffer_action_sensitivities()

    def _remove_document(self, document):
        "_remove_doc", document
        del self._documents[document.unique_id]
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
