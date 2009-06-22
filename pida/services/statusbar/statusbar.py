# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import sys

import gtk
import pango
import locale
import datetime

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.environment import on_windows
# locale
from pida.core.locale import Locale
_locale = Locale('statusbar')
_ = _locale.gettext


class StatusbarEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                self.on_document_changed)
        self.subscribe_foreign('project', 'project_switched',
                self.on_project_switched)
        self.subscribe_foreign('filemanager', 'browsed_path_changed',
                self.on_browsed_path_changed)

    def on_document_changed(self, document):
        if document.is_new:
            self.svc.set_label('document', (_('New Document'),''))
            self.svc.set_label('document_encoding', 'Unknown')
            self.svc.set_label('document_mtime', '')
            self.svc.set_label('document_size', '%d' %0)
        else:
            self.svc.set_label('document', (document.basename, document))
            self.svc.set_label('document_encoding', document.encoding)

            dt = datetime.datetime.fromtimestamp(document.modified_time)
            #FIXME local seems broken on win32 
            if not on_windows:
                text = dt.strftime(locale.nl_langinfo(locale.D_T_FMT))
            else:
                text = dt.strftime('%a, %d %b %Y %H:%M')
            self.svc.set_label('document_mtime', text)
    
            size = document.filesize
            for ext in ['o', 'Ko', 'Mo', 'Go', 'To']:
                if size > 1024 * 10:
                    size = size / 1024
                else:
                    break
            self.svc.set_label('document_size', '%d%s' % (size, ext))

    def on_project_switched(self, project):
        self.svc.set_label('project', project.display_name)

    def on_browsed_path_changed(self, path):
        self.svc.set_label('path', (path, path))


class StatusbarOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_statusbar',
            _('Show the statusbar'),
            bool,
            True,
            _('Whether the statusbar will be shown'),
            self.on_show_ui,
        )

    def on_show_ui(self, option):
        self.svc.show_statusbar(option.value)

class TabLabel(gtk.HBox):

    def __init__(self, icon_name, text, ellipsize=pango.ELLIPSIZE_NONE):
        gtk.HBox.__init__(self, spacing=2)
        if None in [icon_name, text]:
            return None
        self._label = gtk.Label(text)
        self._label.set_padding(5, 5)
        self._label.set_max_width_chars(len(text))
        self._label.set_single_line_mode(True)
        self._label.set_ellipsize(ellipsize)

        self._icon = gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.pack_start(self._icon, expand=False)
        self.pack_start(self._label, expand=True)
        self.show_all()

    def set_text(self, text):
        self._label.set_text(text)
        self._label.set_max_width_chars(len(text))

class StatusMenu(gtk.EventBox):

    def __init__(self, icon_name, text, activate_callback,
                    ellipsize=pango.ELLIPSIZE_NONE ):
        gtk.EventBox.__init__(self)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self._on_eventbox__clicked)
        self.activate_callback = activate_callback
        self._history = []
        self._hb = gtk.HBox(spacing=2)
        self.add(self._hb)
        self._label = gtk.Label(text)
        self._label.set_padding(5, 5)
        self._label.set_ellipsize(ellipsize)
        self._icon = gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._hb.pack_start(self._icon, expand=False)
        self._hb.pack_start(self._label, expand=True)
        self.show_all()

    def set_text(self, (text, value)):
        if value == -1:
            value = text
        self._label.set_text(text)
        if text:
            self.add_history((text, value))

    def add_history(self, (text, value)):
        if (text, value) in self._history:
            self._history.remove((text, value))
        self._history.append((text, value))

    def _on_eventbox__clicked(self, eventbox, event):
        self.popup_menu(event)

    def popup_menu(self, event):
        menu = gtk.Menu()
        for text, value in self._history:
            mi = gtk.MenuItem(text)
            mi.connect('activate', self.activate_callback, value)
            menu.add(mi)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

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
        w = TabLabel('package_utilities','')
        self.add_status('project', widget=w, text='No project')
        w = StatusMenu('file-manager','', self.on_filemanager_history_activate,
                ellipsize=pango.ELLIPSIZE_START)
        self.add_status('path', widget=w, expand=True)
        w = StatusMenu('package_office','', self.on_buffer_history_activate)
        self.add_status('document', widget=w, text='No document')
        w = gtk.Label()
        w.set_padding(5, 0)
        self.add_status('document_mtime', widget=w)
        w = gtk.Label()
        w.set_padding(5, 0)
        self.add_status('document_encoding', widget=w)
        w = gtk.Label()
        w.set_padding(5, 0)
        self.add_status('document_size', widget=w)

    def set_default_values(self):
        project = self.boss.cmd('project', 'get_current_project')
        if project is not None:
            self.set_label('project', project.display_name)
        path = self.boss.cmd('filemanager', 'get_browsed_path')
        self.set_label('path', (path, path))

    def add_status(self, name, widget, text='', expand=False):
        #widget.set_text(text)
        separator = gtk.VSeparator()

        # add in ui
        if self._places:
            self._statusbar.pack_start(separator, expand=False)
        self._statusbar.pack_start(widget, expand=expand, padding=5)
        if self.opt('show_statusbar'):
            self._statusbar.show_all()

        # save in cache
        self._places[name] = {
                'widget':widget,
                '_separator':separator,
            }


    def set_label(self, name, label):
        if hasattr(self, '_places'):
            self._places[name]['widget'].set_text(label)

    def remove_status(self, name):
        if not self._places.has_key(name):
            return
        status = self._places[name]['widget']
        separator = self._places[name]['_separator']
        self._statusbar.remove(status)
        self._statusbar.remove(separator)
        del self._places[name]

    def show_statusbar(self, visibility):
        self.window.set_statusbar_visibility(visibility)

    def on_filemanager_history_activate(self, menuitem, value):
        self.boss.cmd('filemanager', 'browse', new_path=value)
        self.boss.cmd('filemanager', 'present_view')

    def on_buffer_history_activate(self, menuitem, value):
        self.boss.cmd('buffer', 'open_file', file_name=value.filename)


# Required Service attribute for service loading
Service = Statusbar



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
