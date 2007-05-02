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

from kiwi.ui.objectlist import ObjectList, Column, SequentialColumn

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.core.environment import get_uidef_path

from pida.ui.views import PidaView
from pida.utils.unique import create_unique_id

class ChecklistItem(object):

    def __init__(self, title, severity=1, done=False, key=None):
        self.title = title
        self.severity = severity
        self.done = done
        if key is not None:
            self.key = key
        else:
            self.key = str(create_unique_id())


class ChecklistView(PidaView):

    icon_name = 'gtk-todo'
    label_text = 'Check list'

    def create_ui(self):
        self._vbox = gtk.VBox()
        self.create_toolbar()
        self.create_ui_list()
        self.create_newitem()
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

    def create_ui_list(self):
        self._list = ObjectList([
                Column('done', title='Done', data_type=bool, editable=True),
                Column('title', title='Title', data_type=str, editable=True)
                #Column('severity', title='Severity', data_type=int, editable=True)
                ])
        self._list.connect('cell-edited', self._on_item_edit)
        self._list.connect('selection-changed', self._on_item_selected)
        self._list.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._vbox.add(self._list)
        self._list.show_all()

    def create_newitem(self):
        self._hbox = gtk.HBox()
        self._newitem_title = gtk.Entry()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        self._uim.add_ui_from_file(get_uidef_path('checklist-toolbar.xml'))
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()

    def add_item(self, item):
        self._list.append(item, select=True)

    def update_item(self, item):
        self._list.update(item)

    def remove_item(self, item):
        self._list.remove(item)

    def clear(self):
        self._list.clear()

    def _on_item_selected(self, olist, item):
        self.svc.set_current(item)

    def _on_item_edit(self, olist, item, value):
        self.svc.save()

class ChecklistActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_checklist',
            TYPE_TOGGLE,
            'Checklist Viewer',
            'Show checklists',
            '',
            self.on_show_checklist,
            '<Shift><Control>1',
        )

        self.create_action(
            'checklist_add',
            TYPE_NORMAL,
            'Add something in checklist',
            'Add something in checklist',
            gtk.STOCK_ADD,
            self.on_checklist_add,
            'NOACCEL',
        )

        self.create_action(
            'checklist_del',
            TYPE_NORMAL,
            'Delete selected item',
            'Delete selected item',
            gtk.STOCK_DELETE,
            self.on_checklist_del,
            'NOACCEL',
        )



    def on_show_checklist(self, action):
        if action.get_active():
            self.svc.show_checklist()
        else:
            self.svc.hide_checklist()

    def on_checklist_add(self, action):
        self.svc.add_item(ChecklistItem(title='__edit_this__'))

    def on_checklist_del(self, action):
        self.svc.remove_current()


class ChecklistEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('project', 'project_switched',
                                     self.svc.on_project_switched)



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
            data[key] = '%s:%d:%s' % (item.done, item.severity, item.title)
        return data

    def _unserialize(self, data):
        if data == None:
            return
        for key in data:
            line = data[key]
            t = line.rsplit(':',2)
            done = False
            if t[0] == 'True':
                done = True
            self.add_item(ChecklistItem(
                title=str(t[2]),
                severity=int(t[1]),
                done=done,
                key=key))

    def load(self):
        self._items = {}
        self._view.clear()
        data = self.boss.cmd('project', 'get_current_project_data',
                section_name='checklist')
        self._unserialize(data)

    def save(self):
        data = self._serialize()
        self.boss.cmd('project', 'save_to_current_project',
                section_name='checklist', section_data=data)


# Required Service attribute for service loading
Service = Checklist



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
