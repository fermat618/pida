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

from __future__ import with_statement

import gtk
import os
import pkgutil
import pida.utils.serialize as simplejson

from pida.ui.objectlist import AttrSortCombo
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.python import enum

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.ui.views import PidaView, WindowConfig
from pida.utils.unique import create_unique_id

# locale
from pida.core.locale import Locale
locale = Locale('checklist')
_ = locale.gettext

#Critical, Major, Minor, Warning, Normal
class ChecklistStatus(enum):
    (LOW,
     NORMAL,
     HIGH) = range(3)

    def __new__(cls, value, name):
        self = enum.__new__(cls, value, name)
        self.value = value
        return self


class ChecklistItem(object):

    def __init__(self, title, priority=ChecklistStatus.NORMAL, done=False, key=None):
        self.title = title
        self.priority = priority
        self.done = done
        if key is not None:
            self.key = key
        else:
            self.key = str(create_unique_id())


class ChecklistView(PidaView):
    
    key = 'checklist.view'

    icon_name = 'gtk-todo'
    label_text = _('Check list')

    def create_ui(self):
        self._vbox = gtk.VBox(spacing=3)
        self._vbox.set_border_width(3)
        self.create_toolbar()
        self.create_newitem()
        self.create_list()
        self.add_main_widget(self._vbox)
        self._vbox.show_all()

    def create_tab_label(self, icon_name, text):
        if None in [icon_name, text]:
            return None
        label = gtk.Label(text)
        b_factory = gtk.HBox
        b = b_factory(spacing=2)
        icon = gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_MENU)
        b.pack_start(icon)
        b.pack_start(label)
        b.show_all()
        return b

    def create_list(self):
        self._list = ObjectList([
                Column('done', title=_('Done'), data_type=bool, editable=True),
                Column('title', title=_('Title'), data_type=str,
                    editable=True, expand=True),
                Column('priority', title=_('Priority'),
                    data_type=ChecklistStatus, editable=True)
                ])
        self._list.connect('cell-edited', self._on_item_edit)
        self._list.connect('selection-changed', self._on_item_selected)
        self._list.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._vbox.add(self._list)

        self._sort_combo = AttrSortCombo(self._list,
            [
                ('done', _('Done')),
                ('title', _('Title')),
                ('priority', _('Priority')),
            ],
            'title')

        self._vbox.pack_start(self._sort_combo, expand=False)
        self._list.show_all()
        self._sort_combo.show_all()

    def create_newitem(self):
        self._hbox = gtk.HBox(spacing=3)
        self._newitem_title = gtk.Entry()
        self._newitem_title.connect('changed', self._on_newitem_changed)
        self._newitem_ok = gtk.Button(stock=gtk.STOCK_ADD)
        self._newitem_ok.connect('clicked', self._on_item_add)
        self._newitem_ok.set_sensitive(False)
        self._hbox.pack_start(self._newitem_title, expand=True)
        self._hbox.pack_start(self._newitem_ok, expand=False)
        self._vbox.pack_start(self._hbox, expand=False)
        self._hbox.show_all()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        uim_data = pkgutil.get_data(__name__, 'uidef/checklist-toolbar.xml')
        self._uim.add_ui_from_string(uim_data)
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._vbox.pack_start(self._toolbar, expand=False)
        self.svc.get_action('checklist_del').set_sensitive(False)
        self._toolbar.show_all()

    def add_item(self, item):
        self._list.append(item, select=True)
        self.svc.save()

    def update_item(self, item):
        self._list.update(item)
        self.svc.save()

    def remove_item(self, item):
        self._list.remove(item)
        self.svc.save()

    def clear(self):
        self._list.clear()

    def _on_item_selected(self, olist, item):
        self.svc.get_action('checklist_del').set_sensitive(item is not None)
        self.svc.set_current(item)

    def _on_item_edit(self, olist, item, value):
        self.svc.save()

    def _on_item_add(self, w):
        title = self._newitem_title.get_text()
        self.svc.add_item(ChecklistItem(title=title))
        self._newitem_title.set_text('')

    def _on_newitem_changed(self, w):
        self._newitem_ok.set_sensitive(self._newitem_title.get_text() != '')

    def can_be_closed(self):
        self.svc.get_action('show_checklist').set_active(False)


class ChecklistActions(ActionsConfig):

    def create_actions(self):
        ChecklistWindowConfig.action = self.create_action(
            'show_checklist',
            TYPE_REMEMBER_TOGGLE,
            _('Checklist Viewer'),
            _('Show checklists'),
            '',
            self.on_show_checklist,
            '',
        )

        self.create_action(
            'checklist_add',
            TYPE_NORMAL,
            _('Add something in checklist'),
            _('Add something in checklist'),
            gtk.STOCK_ADD,
            self.on_checklist_add,
              
        )

        self.create_action(
            'checklist_del',
            TYPE_NORMAL,
            _('Delete selected item'),
            _('Delete selected item'),
            gtk.STOCK_DELETE,
            self.on_checklist_del,
        )



    def on_show_checklist(self, action):
        if action.get_active():
            self.svc.show_checklist()
        else:
            self.svc.hide_checklist()

    def on_checklist_add(self, action):
        self.svc.add_item(ChecklistItem(title=_('__edit_this__')))

    def on_checklist_del(self, action):
        self.svc.remove_current()


class ChecklistEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
                               self.svc.on_project_switched)


class ChecklistWindowConfig(WindowConfig):
    key = ChecklistView.key
    label_text = ChecklistView.label_text

class ChecklistFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            ChecklistWindowConfig)


# Service class
class Checklist(Service):
    """Manage checklists"""

    actions_config = ChecklistActions
    events_config = ChecklistEvents

    def start(self):
        self._view = ChecklistView(self)
        self._has_loaded = False
        self._items = {}
        self._current = None
        self._project = None

    def show_checklist(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_checklist(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def set_current(self, item):
        self._current = item

    def remove_current(self):
        if self._current == None:
            return
        del self._items[self._current.key]
        self._view.remove_item(self._current)
        self._current = None
        self.save()

    def add_item(self, item):
        self._items[item.key] = item
        self._view.add_item(item)
        self.save()

    def update_item(self, item, value):
        item.title = value
        self._items[item.key] = item
        self._view.update_item(item)
        self.save()

    def on_project_switched(self, project):
        if project != self._project:
            self._project = project
            self.load()

    def _serialize(self):
        data = {}
        for key in self._items:
            item = self._items[key]
            data[key] = dict(done=item.done, 
                             prio=item.priority.value, 
                             title=item.title)
        return data

    def _unserialize(self, data):
        if data == None:
            return
        for key in data:
            line = data[key]
            t = data[key]
            self.add_item(ChecklistItem(
                title=str(t['title']),
                priority=ChecklistStatus.get(int(t['prio'])),
                done=bool(t['done']),
                key=key))

    def load(self):
        if not self.started:
            return
        self._items = {}
        self._view.clear()
        fname = self._project.get_meta_dir('checklist', filename="data.json")
        if not os.path.exists(fname):
            return
        with open(fname, "r") as fp:
            data = simplejson.load(fp)
            if data:
                self._unserialize(data)

    def save(self):
        fname = self._project.get_meta_dir('checklist', filename="data.json")
        with open(fname, "w") as fp:
            data = self._serialize()
            if data:
                simplejson.dump(data, fp)

    def stop(self):
        if self.get_action('show_checklist').get_active():
            self.hide_checklist()


# Required Service attribute for service loading
Service = Checklist



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
