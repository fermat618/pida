# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

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

import gtk

from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.commands import CommandsConfig
from pida.core.service import Service

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
        )

        self.create_action(
            'redo',
            TYPE_NORMAL,
            _('Redo'),
            _('Redo the last editor action'),
            gtk.STOCK_REDO,
            self.on_redo,
        )

        self.create_action(
            'cut',
            TYPE_NORMAL,
            _('Cut'),
            _('Cut the selection in the editor'),
            gtk.STOCK_CUT,
            self.on_cut,
        )

        self.create_action(
            'copy',
            TYPE_NORMAL,
            _('Copy'),
            _('Copy the selection in the editor'),
            gtk.STOCK_COPY,
            self.on_copy,
        )

        self.create_action(
            'paste',
            TYPE_NORMAL,
            _('Paste'),
            _('Paste the clipboard in the editor'),
            gtk.STOCK_PASTE,
            self.on_paste,
        )

        self.create_action(
            'save',
            TYPE_NORMAL,
            _('Save'),
            _('Save the current document'),
            gtk.STOCK_SAVE,
            self.on_save,
        )

        self.create_action(
            'focus_editor',
            TYPE_NORMAL,
            _('Focus Editor'),
            _('Focus the editor component window'),
            'application-edit',
            self.on_focus_editor,
            '<Shift><Control>e',
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

class EditorCommandsConfig(CommandsConfig):

    def open(self, document):
        self.svc.open(document)

    def close(self, document):
        self.svc.close(document)

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

    def grab_focus(self):
        self.svc.grab_focus()

    def delete_current_word(self):
        self.svc.delete_current_word()

    def insert_text(self, text):
        self.svc.insert_text(text)


class EditorService(Service):
    
    actions_config = EditorActionsConfig
    commands_config = EditorCommandsConfig

    @classmethod
    def get_sanity_errors(cls):
        return []




# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
