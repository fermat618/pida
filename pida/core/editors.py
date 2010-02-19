# -*- coding: utf-8 -*-
"""
    Editor Base Classes
    ~~~~~~~~~~~~~~~~~~~

    They provide the basic setup for all editors.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)

"""

import gtk
import gobject

from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.commands import CommandsConfig
from pida.core.service import Service
from pida.core.document import DocumentException

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class EditorActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'undo',
            TYPE_NORMAL,
            _('Undo'),
            _('Undo the last editor action'),
            gtk.STOCK_UNDO,
            self.on_undo,
            '<Shift><Control><Alt>Z',
        )

        self.create_action(
            'redo',
            TYPE_NORMAL,
            _('Redo'),
            _('Redo the last editor action'),
            gtk.STOCK_REDO,
            self.on_redo,
            '<Shift><Control><Alt>Y',
        )

        self.create_action(
            'cut',
            TYPE_NORMAL,
            _('Cut'),
            _('Cut the selection in the editor'),
            gtk.STOCK_CUT,
            self.on_cut,
            '<Shift><Control><Alt>X',
        )

        self.create_action(
            'copy',
            TYPE_NORMAL,
            _('Copy'),
            _('Copy the selection in the editor'),
            gtk.STOCK_COPY,
            self.on_copy,
            '<Shift><Control><Alt>C',
        )

        self.create_action(
            'paste',
            TYPE_NORMAL,
            _('Paste'),
            _('Paste the clipboard in the editor'),
            gtk.STOCK_PASTE,
            self.on_paste,
            '<Shift><Control><Alt>V',
        )

        self.create_action(
            'save',
            TYPE_NORMAL,
            _('Save'),
            _('Save the current document'),
            gtk.STOCK_SAVE,
            self.on_save,
            '<Shift><Control><Alt>S',
        )

        self.create_action(
            'focus_editor',
            TYPE_NORMAL,
            _('Focus Editor'),
            _('Focus the editor component window'),
            'application-edit',
            self.on_focus_editor,
            '<Shift><Control>e',
            global_=True
        )


    def on_undo(self, action):
        self.svc.undo()

    def on_redo(self, action):
        self.svc.redo()

    def on_cut(self, action):
        self.svc.cut()

    def on_copy(self, action):
        self.svc.copy()

    def on_paste(self, action):
        self.svc.paste()

    def on_save(self, action):
        self.svc.save()

    def on_focus_editor(self, action):
        self.svc.grab_focus()
        self.svc.window.present()

class EditorCommandsConfig(CommandsConfig):

    def open(self, document):
        self.svc.open(document)

    def open_list(self, documents):
        self.svc.open_list(documents)

    def close(self, document):
        return self.svc.close(document)

    def goto_line(self, line):
        self.svc.goto_line(line)

    def define_sign_type(self, type, icon, linehl, text, texthl):
        self.svc.define_sign_type(type, icon, linehl, text, texthl)

    def undefine_sign_type(self, type):
        self.svc.undefine_sign_type(type)

    def get_current_line_number(self):
        return self.svc.get_current_line()

    def show_sign(self, type, file_name, line):
        self.svc.show_sign(type, file_name, line)

    def hide_sign(self, type, file_name, line):
        self.svc.hide_sign(type, file_name, line)

    def call_with_current_word(self, callback):
        self.svc.call_with_current_word(callback)

    def call_with_selection(self, callback):
        self.svc.call_with_selection(callback)

    def call_with_selection_or_word(self, callback):
        self.svc.call_with_selection_or_word(callback)

    def grab_focus(self):
        self.svc.grab_focus()

    def delete_current_word(self):
        self.svc.delete_current_word()

    def insert_text(self, text):
        self.svc.insert_text(text)


class EditorService(Service):

    actions_config = EditorActionsConfig
    commands_config = EditorCommandsConfig

    def __repr__(self):
        return '<Editor: %s>' % self.__class__.__name__

    def _open_single(self, docs):
        if not docs:
            # return fales to be not called anymore
            return False
        try:
            self.open(docs.pop())
        except DocumentException, err:
            self.log.exception(err)
            self.emit('document-exception', error=err)
        return True

    def open_list(self, documents):
        #XXX: this way is not acceptable, and only the fallback
        # solution for editors not implementing the open_list interface

        # make a copy of the file list as we modify it and
        # this could cause side effects very hard to debug
        documents_c = documents[:]
        gobject.timeout_add(100, self._open_single, documents_c)

    @classmethod
    def get_sanity_errors(cls):
        return []


LINEMARKER_TYPES = [
'bookmark',
'debugger_breakpoint',
'debugger_position',
]

class LineMarker(object):
    """
    LineMarker is a class used to mark lines with specific informations
    like bookmarks, breakpoints etc.

    LineMarkers are managed through an MarkerInterface instance.

    If a LineMark is marked for beeing deleted it's line number is
    changed to -1.

    """
    def __init__(self, filename, lineno, type_):
        self.filename = filename
        self._lineno = lineno
        assert type_ in LINEMARKER_TYPES
        self.type_ = type_

    def set_line(self, newlineno):
        newlineno = int(newlineno)

        if self._lineno != newlineno:
            self.update(newlineno)
            #self._lineno = newlineno

    def get_line(self):
        return int(self._lineno)

    line = property(get_line, set_line)

    def update(self, newlineno):
        """
        This function is called when the lineno changes. This should update
        the views etc.

        Must be overloaded by the real implementation.
        """
        pass

    def __repr__(self):
        return '<LineMarker %s %s>' % (self.filename, self._lineno)

class MarkerInterface(object):
    """
    The MarkerInterface is used by the editor component to
    receive LineMarkers from a plugin.

    To register a MakerInterface put an in the features of the Editor.
    """

    def get_line_markers(self, filename):
        raise NotImplemented

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
