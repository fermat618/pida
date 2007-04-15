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

import sys, compiler

import gtk

from kiwi.ui.objectlist import ObjectList, Column


# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig

from pida.ui.views import PidaView

from pida.utils import pyflakes
from pida.utils.gthreads import AsyncTask, gcall

class PyflakeView(PidaView):
    
    icon_name = 'error'
    label_text = 'Python Errors'

    def create_ui(self):
        self.errors_ol = ObjectList(
            Column('markup', use_markup=True)
        )
        self.errors_ol.set_headers_visible(False)
        self.add_main_widget(self.errors_ol)
        self.errors_ol.show_all()

    def clear_items(self):
        self.errors_ol.clear()

    def set_items(self, items):
        self.clear_items()
        for item in items:
            self.errors_ol.append(self.decorate_pyflake_message(item))

    def decorate_pyflake_message(msg):
        args = [('<b>%s</b>' % arg) for arg in msg.message_args]
        message_string = msg.message % tuple(args)
        msg.markup = ('<tt>%s </tt><i>%s</i>\n%s' % 
                      (msg.lineno, msg.__class__.__name__, message_string))
        return msg



class Pyflaker(object):

    def __init__(self, svc):
        self.svc = svc
        self._view = PyflakeView(self.svc)
        self.svc.boss.add_view('Plugin', self._view)

    def set_current_document(self, document):
        self._current = document
        self.refresh_view()

    def refresh_view(self):
        task = AsyncTask(self.check_current, self.set_view_items)
        task.start()

    def check_current(self):
        return self.check(self._current)

    def check(self, document):
        code_string = document.string
        filename = document.filename
        try:
            tree = compiler.parse(code_string)
        except (SyntaxError, IndentationError), e:
            msg = e
            msg.name = e.__class__.__name__
            value = sys.exc_info()[1]
            (lineno, offset, line) = value[1][1:]
            if line.endswith("\n"):
                line = line[:-1]
            msg.lineno = lineno
            msg.message_args = (line,)
            msg.message = '<tt>%%s</tt>\n<tt>%s^</tt>' % (' ' * (offset - 2))
            return [msg]
        else:
            w = pyflakes.Checker(tree, filename)
            return w.messages

    def set_view_items(self, items):
        self._view.set_items(items)
        

class PythonEventsConfig(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed', self.on_document_changed)

    def on_document_changed(self, document):
        self.svc.set_current_document(document)

# Service class
class Python(Service):
    """Describe your Service Here""" 

    events_config = PythonEventsConfig

    def start(self):
        """Start the service"""
        self._current = None
        self._pyflaker = Pyflaker(self)

    def set_current_document(self, document):
        self._current = document
        self._pyflaker.set_current_document(document)

# Required Service attribute for service loading
Service = Python



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
