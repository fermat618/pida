# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# stdlib
import os.path

# gtk
import gtk, gobject

# PIDA Imports

# core

from kiwi.ui.objectlist import Column

from pida.core.service import Service

from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import (ActionsConfig, TYPE_NORMAL)
from pida.core.options import OptionsConfig
from pida.ui.views import PidaGladeView, WindowConfig
from pida.services.language import DOCTYPES
from pida.core.projects import RESULT
from pida.utils.gthreads import gcall
import time


# locale
from pida.core.locale import Locale
locale = Locale('')
_ = locale.gettext

class QItem(object):
    name = ''
    path = ''

class QOpenView(PidaGladeView):

    key = 'qopen.view'
    gladefile = 'qopen'
    label_text = _('Quick Open')

    def create_ui(self):
        self._history = gtk.ListStore(gobject.TYPE_STRING)
        self.filter.set_model(self._history)
        self.filter.set_text_column(0)
        self.last_entered = 0
        self.olist.set_columns(
            [
                Column('basename', title=_('Name')),
                Column('relpath', title=_('Path')),
            ]
        )
        self.olist.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.filter.child.connect("changed", self.on_filter_changed)
        self.filter.child.connect("activate", self.on_filter_activate)
        self.filter.child.connect("key-press-event", self.on_filter_keypress)
        #self.toplevel.connect_after("map", self.on_show)
        self.filter.connect_after("map", self.on_show)

    def set_filter(self, text, time_check=None):
        if time_check and self.last_entered > time_check:
            return False
        self._history.insert(0, (text,))
        self.olist.clear()
        tokens = text.split()
        if not len(tokens):
            return
        ftypes = []
        fnames = []
        fall = []
        filters = self.svc.boss.get_service('filemanager').\
                                   features['file_hidden_check']
        for tok in tokens:
            if not tok:
                continue
            if tok[0] == "#" and len(tok) > 1:
                for lang in DOCTYPES.get_fuzzy_list(tok[1:]):
                    ftypes.append(lang.internal)
            elif tok[0] == "!" and len(tok) > 1:
                fnames.append(tok[1:])
            else:
                fall.append(tok)

        def do_filter(item):
            if len(self.olist) > 200:
                RESULT.ABORT
            if not len(item.basename) or not len(item.relpath):
                return
            if "/." in item.relpath or item.relpath[0] == ".":
                return
            for chk in filters:
                if not chk(item.basename, item.relpath, ''):
                    return
            if item.is_dir:
                return
            if all((x in item.relpath for x in fall)) and \
               all((x in item.basename for x in fnames)):
                if len(ftypes):
                    if item.doctype in ftypes:
                        return RESULT.YES
                else:
                    return RESULT.YES

        project = self.svc.boss.cmd('project', 'get_current_project')
        if not project:
            return
        for result in project.query(do_filter):
            self.olist.append(result)

        return False

    def on_show(self, *args):
        gcall(self.filter.child.grab_focus)

    def on_olist__key_press_event(self, widget, event):
        if event.keyval == gtk.keysyms.Escape and self.pane.get_params().detached:
            self.can_be_closed()

    def on_filter_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Tab and len(self.olist):
            gcall(self.olist.grab_focus)
        if event.keyval == gtk.keysyms.Escape and self.pane.get_params().detached:
            self.can_be_closed()

    def on_filter_activate(self, *args):
        if len(self.olist):
            self.svc.open(self.olist[0])

    def on_filter_changed(self, *args):
        self.last_entered = time.time()
        gobject.timeout_add(self.svc.opt('start_delay'), 
                            self.set_filter, self.filter.child.props.text, 
                            self.last_entered)

    def on_olist__row_activated(self, widget, item):
        self.svc.open(item)

    def on_button_open__clicked(self, button):
        for item in self.olist.get_selected_rows():
            self.svc.open(item)
        if self.pane.get_params().detached:
            self.on_button_close__clicked(button)

    def can_be_closed(self):
        self.svc.boss.cmd('window', 'remove_view', view=self)

    def on_button_close__clicked(self, button):
        self.svc.boss.cmd('window', 'remove_view', view=self)

class QopenEventsConfig(EventsConfig):

    def create(self):
        #self.publish('something')
        pass

    def subscribe_all_foreign(self):
        #self.subscribe_foreign('buffer', 'document-changed',
        #            self.on_document_changed)
        pass

    def on_document_changed(self, document):
        pass

class QopenWindowConfig(WindowConfig):
    key = QOpenView.key
    label_text = QOpenView.label_text

class QopenFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
                QopenWindowConfig)


class QopenOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'start_delay',
            _('Start after'),
            int, # type of variable, like int, str, bool, ..
            800,
            _('Start search after n milliseconds'),
        )


class QopenActionsConfig(ActionsConfig):

    def create_actions(self):
        QopenWindowConfig.action = self.create_action(
            'qopen_show',
            TYPE_NORMAL,
            _('Open in project'),
            _('Open file in project.'),
            gtk.STOCK_OPEN,
            self.on_qopen_show,
            ''  # default shortcut or '' to enable shortcut for action
        )

    def on_qopen_show(self, action):
        self.svc.show_qopen()




class QuickOpen(Service):

    #features_config = QopenFeaturesConfig
    actions_config = QopenActionsConfig
    options_config = QopenOptionsConfig
    #events_config = QopenEventsConfig
    label = "Quick Open"

    def pre_start(self):
        self._view = None
        pass

    def start(self):
        pass
        
    def stop(self):
        pass

    def show_qopen(self):
        if not self._view:
            self._view = QOpenView(self)
        if not self.boss.cmd('window', 'is_added', view=self._view):
            self.boss.cmd('window', 'add_detached_view', 
                          paned='Buffer', view=self._view,
                          )
        else:
            self.boss.cmd('window', 'present_view', view=self._view)

    def open(self, item):
        project = self.boss.cmd('project', 'get_current_project')
        if not project:
            return
        path = os.path.join(project.source_directory, item.relpath)
        if item.is_dir:
            self.boss.cmd('filemanager', 'browse', new_path=path)
            self.boss.cmd('filemanager', 'present_view')
        else:
            self.boss.cmd('buffer', 'open_file', file_name=path)

# Required Service attribute for service loading
Service = QuickOpen



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
