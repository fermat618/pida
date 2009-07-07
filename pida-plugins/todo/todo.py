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


from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.ui.views import PidaView, WindowConfig

from pida.utils.gthreads import GeneratorTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('todo')
_ = locale.gettext

class TodoItem(object):

    def __init__(self, todo, line, marker):
        self.todo = todo
        self.line = line
        self.marker = marker

class TodoView(PidaView):

    key = 'todo.list'

    label_text = _('TODO')
    icon_name =  'accessories-text-editor'

    def create_ui(self):
        self.todo_list = ObjectList(
            [
                Column('line', sorted=True),
                Column('todo'),
                Column('marker'),
            ]
        )
        self.todo_list.connect('double-click', self._on_todo_double_click)
        self.add_main_widget(self.todo_list)
        self.todo_list.show_all()

    def clear_items(self):
        gcall(self.todo_list.clear)

    def add_item(self, todo, line, marker):
        self.todo_list.append(TodoItem(todo, line, marker))

    def _on_todo_double_click(self, olist, item):
        self.svc.boss.editor.cmd('goto_line', line=item.line)

    def can_be_closed(self):
        self.svc.get_action('show_todo').set_active(False)


class TodoActionsConfig(ActionsConfig):

    def create_actions(self):
        TodoWindowConfig.action = self.create_action(
            'show_todo',
            TYPE_REMEMBER_TOGGLE,
            _('Todo Viewer'),
            _('Show the Todo Viewer'),
            'accessories-text-editor',
            self.on_show_todo,
            '<Shift><Control>d',
        )

    def on_show_todo(self, action):
        if action.get_active():
            self.svc.show_todo()
        else:
            self.svc.hide_todo()

class TodoEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                                     self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-saved',
                                     self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_current_document(document)

class TodoWindowConfig(WindowConfig):
    key = TodoView.key
    label_text = TodoView.label_text

class TodoFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            TodoWindowConfig)

# Service class
class Todo(Service):
    """Describe your Service Here""" 

    actions_config = TodoActionsConfig
    events_config = TodoEventsConfig
    features_config = TodoFeaturesConfig

    _markers = ['TODO', 'XXX', 'FIXME']

    def start(self):
        self._current = None
        self._view = TodoView(self)

    def show_todo(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_todo(self):
        self.boss.cmd('window','remove_view', view=self._view)

    def check_current(self):
        for row in self.check_document(self._current):
            yield row

    def find_markers_in_comment(self, line_enumeration_number, comment):
        for marker in self._markers:
            if marker in comment:
                pre, post = comment.split(marker, 1)
                todo = post.strip().strip(':').strip()
                yield (todo, line_enumeration_number + 1, marker)

    def check_document(self, document):
        """Check comments and documentation strings for TODO messages."""
        self._view.clear_items()
        if not document or not document.lines:
            return

        # Use pygments to find a lexer to search within comments.
        # If we don't get a lexer, just search every document line
        # for messages.
        lexer = None
        try:
            from pygments.lexers import get_lexer_for_mimetype
            from pygments.token import String
            from pygments.token import Token

            if document.doctype:
                mimes = document.doctype.mimes

                for m in mimes:
                    try:
                        lexer = get_lexer_for_mimetype(m)
                    except:
                        lexer = None
                        self.log("Failed to get lexer for mimetype (%s)." % m)
                    else:
                        if not lexer == None:
                            break
        except:
            lexer = None
            self.log("Pygments isn't available.  Using simple search.")

        if lexer:
            for i, line in enumerate(document.lines):
                for n, m in lexer.get_tokens(line):
                    if n == Token.Comment or n == String.Doc:
                        for marker in self.find_markers_in_comment(i, m):
                            yield marker
        else:
            for i, line in enumerate(document.lines):
                for marker in self.find_markers_in_comment(i, line):
                    yield marker

    def add_todo_item(self, todo, line, marker):
        self._view.add_item(todo, line, marker)

    def set_current_document(self, document):
        self._current = document
        if self._current is not None:
            task = GeneratorTask(self.check_current, self.add_todo_item)
            task.start()

    def stop(self):
        if self.get_action('show_todo').get_active():
            self.hide_todo()


# Required Service attribute for service loading
Service = Todo



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
