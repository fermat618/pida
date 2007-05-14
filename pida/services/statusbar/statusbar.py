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
import locale
import datetime

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, OTypeBoolean
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

# locale
from pida.core.locale import Locale
_locale = Locale('statusbar')
_ = _locale.gettext


class StatusbarEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
                self.on_document_changed)
        self.subscribe_foreign_event('project', 'project_switched',
                self.on_project_switched)
        self.subscribe_foreign_event('filemanager', 'browsed_path_changed',
                self.on_browsed_path_changed)

    def on_document_changed(self, document):
        self.svc.set_label('document', document.get_basename())
        self.svc.set_label('document_encoding', document.get_encoding())

        dt = datetime.datetime.fromtimestamp(document.get_mtime())
        text = dt.strftime(locale.nl_langinfo(locale.D_T_FMT))
        self.svc.set_label('document_mtime', text)

        size = document.get_size()
        for ext in ['o', 'Ko', 'Mo', 'Go', 'To']:
            if size > 1024 * 10:
                size = size / 1024
            else:
                break
        self.svc.set_label('document_size', '%d%s' % (size, ext))

    def on_project_switched(self, project):
        self.svc.set_label('project', project.get_name())

    def on_browsed_path_changed(self, path):
        self.svc.set_label('path', path)


class StatusbarOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_statusbar',
            _('Show the statusbar'),
            OTypeBoolean,
            True,
            _('Whether the statusbar will be shown'),
            self.on_show_ui,
        )

    def on_show_ui(self, client, id, entry, option):
        self.svc.show_statusbar(option.get_value())

class TabLabel(gtk.HBox):

    def __init__(self, icon_name, text):
        gtk.HBox.__init__(self, spacing=2)
        if None in [icon_name, text]:
            return None
        self.__label = gtk.Label(text)
        self.__label.set_padding(5, 5)
        self.__icon = gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.pack_start(self.__icon, expand=False)
        self.pack_start(self.__label, expand=False)
        self.show_all()

    def set_text(self, text):
        self.__label.set_text(text)

# Service class
class Statusbar(Service):
    """PIDA Statusbar"""

    options_config = StatusbarOptionsConfig
    events_config = StatusbarEvents

    def start(self):
        self._statusbar = self.window.get_statusbar()
        self._places = {}
        self.create_ui()
        self.set_default_values()
        self.show_statusbar(self.opt('show_statusbar'))

    def create_ui(self):
        self._statusbar.insert(gtk.SeparatorToolItem(), -1)
        w = TabLabel('package_utilities','')
        self.add_status('project', widget=w, text='No project')
        w = TabLabel('file-manager','')
        self.add_status('path', widget=w, expand=True)
        w = TabLabel('package_office','')
        self.add_status('document', widget=w, text='No document', expand=True)
        w = gtk.Label()
        w.set_padding(3, 0)
        self.add_status('document_mtime', widget=w)
        w = gtk.Label()
        w.set_padding(3, 0)
        self.add_status('document_encoding', widget=w)
        w = gtk.Label()
        w.set_padding(3, 0)
        self.add_status('document_size', widget=w)

    def set_default_values(self):
        project = self.boss.cmd('project', 'get_current_project')
        if project is not None:
            self.set_label('project', project.get_name())
        path = self.boss.cmd('filemanager', 'get_browsed_path')
        self.set_label('path', path)

    def add_status(self, name, widget, text='-', expand=False):
        toolitem = gtk.ToolItem()
        toolitem.add(widget)
        toolitem.set_expand(expand)
        widget.set_text(text)
        separator = gtk.SeparatorToolItem()

        # add in ui
        self._statusbar.insert(toolitem, -1)
        self._statusbar.insert(separator, -1)
        if self.opt('show_statusbar'):
            self._statusbar.show_all()

        # save in cache
        self._places[name] = {
                'widget':widget,
                'toolitem':gtk.ToolItem(),
            }
        self._places['_separator_'+name] = {
                'widget':separator,
                'toolitem':separator,
            }


    def set_label(self, name, label):
        if hasattr(self, '_places'):
            self._places[name]['widget'].set_text(label)

    def remove_status(self, name):
        if not self._places.has_key(name):
            return
        status = self._places[name]
        separator = self._places['_separator_'+name]
        self._statusbar.remove(status['toolitem'])
        self._statusbar.remove(separator['toolitem'])
        del self._places[name]
        del self._places['_separator_'+name]

    def show_statusbar(self, visibility):
        self.window.set_statusbar_visibility(visibility)


# Required Service attribute for service loading
Service = Statusbar



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
