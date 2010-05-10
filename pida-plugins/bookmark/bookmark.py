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
import os
import cgi
import pkgutil

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.core.editors import LineMarker, MarkerInterface

from pida.ui.views import PidaView, WindowConfig

from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall

import pida.utils.serialize as simplejson

# locale
from pida.core.locale import Locale
locale = Locale('bookmark')
_ = locale.gettext

class BookmarkItem(object):
    group = None
    keys = 'data', 'group', 'title'
    def __init__(self, title, data):
        self.title = title
        self.data = data

    def run(self, service):
        pass

    def _key(self):
        return tuple(getattr(self, key) for key in self.keys)

    def __hash__(self):
        return hash(self._key())

    def __cmp__(self, other):
        return cmp(hash(self),hash(other))


class BookmarkItemFile(BookmarkItem, LineMarker):
    group = 'file'
    keys = BookmarkItem.keys + ('line',)
    type = 'bookmark'

    def __init__(self, svc, data=None, line=1):
        #self.line = line
        self.svc = svc
        BookmarkItem.__init__(self,  title='', data=data)
        self.data = data
        self._lineno = line

    def _get_title(self):
        try:
            color = self.svc._view._list['file'].style.lookup_color('pida-lineno').\
                    to_string()
        except:
            color = "black"
        try:
            line = int(self.line)
        except ValueError:
            line = 1
        return '%s:<span color="%s">%d</span>' % (
                cgi.escape(os.path.basename(self.data)), color, line)

    def _set_title(self, value): pass

    title = property(_get_title, _set_title)

    def run(self, service):
        service.boss.cmd('buffer', 'open_file', 
                         file_name=self.data, line=self.line)

    def _get_filename(self):
        return self.data

    def _set_filename(self, value):
        self.data = value

    filename = property(_get_filename, _set_filename)

    def _do_set_line(self, newlineno):
        self._lineno = min(1, int(newlineno))
        self.svc._view._list['file'].update(self)

    def update(self, newlineno):
        gcall(self._do_set_line, newlineno)

class BookmarkItemPath(BookmarkItem):
    group = 'path'
    ICON_NAME = 'folder'

    def __init__(self, title='no title', data=None):
        BookmarkItem.__init__(self,  title=title, data=data)

    def run(self, service):
        service.boss.cmd('filemanager', 'browse', new_path=self.data)
        service.boss.cmd('filemanager', 'present_view')

"""
class BookmarkItemUrl(BookmarkItem):
    group = 'url'
    ICON_NAME = 'www'

    def __init__(self, title='no title', data=None):
        BookmarkItem.__init__(self, title=title, data=data)

    def run(self, service):
        service.boss.call_command('browseweb', 'browse', url=self.data)
"""


class BookmarkView(PidaView):

    key = 'bookmark.view'

    icon_name = 'gtk-library'
    label_text = _('Bookmarks')

    def create_ui(self):
        self._vbox = gtk.VBox()
        self.create_toolbar()
        self.create_ui_list()
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

    def create_objectlist(self, icon_name, text):
            l = ObjectList([Column('title', use_markup=True)])
            l.connect('row-activated', self._on_item_activated)
            l.connect('selection-changed', self._on_item_selected)
            l.set_headers_visible(False)
            l.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self._books.append_page(l,
                    tab_label=self.create_tab_label(icon_name, text))
            return l

    def create_ui_list(self):
        self._books = gtk.Notebook()
        self._books.set_border_width(6)
        self._list = {}
        self._list['file'] = self.create_objectlist('text-x-generic', _('Files'))
        self._list['path'] = self.create_objectlist('stock_folder', _('Dirs'))
        """
        self._list_url = ObjectList([Column('markup', data_type=str, use_markup=True)])
        self._list_url.set_headers_visible(False)
        self._books.add(self._list_url)
        """
        self._vbox.add(self._books)
        self._books.show_all()

    def create_toolbar(self):
        self._uim = gtk.UIManager()
        self._uim.insert_action_group(self.svc.get_action_group(), 0)
        uidef_data = pkgutil.get_data(__name__, 'uidef/bookmark-toolbar.xml')
        self._uim.add_ui_from_string(uidef_data)
        self._uim.ensure_update()
        self._toolbar = self._uim.get_toplevels('toolbar')[0]
        self._toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        self._vbox.pack_start(self._toolbar, expand=False)
        self._toolbar.show_all()

    def add_item(self, item):
        self._list[item.group].append(item)

    def remove_item(self, item):
        self._list[item.group].remove(item)

    def clear_all(self):
        for l in self._list.values():
            l.clear()

    def can_be_closed(self):
        self.svc.get_action('show_bookmark').set_active(False)

    def _on_item_selected(self, olist, item):
        self.svc.set_current(item)

    def _on_item_activated(self, olist, item):
        item.run(self.svc)

class BookmarkActions(ActionsConfig):

    def create_actions(self):
        BookmarkWindowConfig.action = self.create_action(
            'show_bookmark',
            TYPE_REMEMBER_TOGGLE,
            _('Bookmark Viewer'),
            _('Show bookmarks'),
            '',
            self.on_show_bookmark,
            '',
        )

        self.create_action(
            'bookmark_curfile',
            TYPE_NORMAL,
            _('Bookmark current file'),
            _('Bookmark current file'),
            'text-x-generic',
            self.on_bookmark_curfile,
            ''
        )

        self.create_action(
            'bookmark_togglefile',
            TYPE_NORMAL,
            _('Toggle Bookmark on current file'),
            _('Toggle Bookmark on current file'),
            'text-x-generic',
            self.on_bookmark_togglefile,
            ''
        )


        self.create_action(
            'bookmark_curdir',
            TYPE_NORMAL,
            _('Bookmark current directory'),
            _('Bookmark current directory'),
            'stock_folder',
            self.on_bookmark_curdir,
            ''
        )

        self.create_action(
            'bookmark_delsel',
            TYPE_NORMAL,
            _('Delete selected item'),
            _('Delete selected item'),
            gtk.STOCK_DELETE,
            self.on_bookmark_delsel,
            ''
        )

        self.create_action(
            'bookmark_go_prev',
            TYPE_NORMAL,
            _('Goto previous bookmark'),
            _('Goto previous bookmark'),
            gtk.STOCK_GO_UP,
            self.on_bookmark_go_prev,
            ''
        )

        self.create_action(
            'bookmark_go_next',
            TYPE_NORMAL,
            _('Goto next bookmark'),
            _('Goto next bookmark'),
            gtk.STOCK_GO_DOWN,
            self.on_bookmark_go_next,
            ''
        )

        self.create_action(
            'bookmark-for-dir',
            TYPE_NORMAL,
            _('Add as bookmark'),
            _('Add selected directory as bookmark'),
            gtk.STOCK_ADD,
            self.on_bookmark_for_dir,
        )

        self.create_action(
            'bookmark-for-file',
            TYPE_NORMAL,
            _('Add as bookmark'),
            _('Add selected file as bookmark'),
            gtk.STOCK_ADD,
            self.on_bookmark_for_file,
        )


    def on_show_bookmark(self, action):
        if action.get_active():
            self.svc.show_bookmark()
        else:
            self.svc.hide_bookmark()

    def on_bookmark_curdir(self, action):
        self.svc.bookmark_dir()

    def on_bookmark_curfile(self, action):
        self.svc.bookmark_file()

    def on_bookmark_togglefile(self, action):
        self.svc.bookmark_toggle_file()

    def on_bookmark_delsel(self, action):
        self.svc.remove_current()

    def on_bookmark_go_next(self, action):
        self.svc.goto_next()

    def on_bookmark_go_prev(self, action):
        self.svc.goto_prev()

    def on_bookmark_for_file(self, action):
        self.svc.bookmark_file(filename=action.contexts_kw['file_name'])

    def on_bookmark_for_dir(self, action):
        self.svc.bookmark_dir(path=action.contexts_kw['dir_name'])

class BookmarkWindowConfig(WindowConfig):
    key = BookmarkView.key
    label_text = BookmarkView.label_text

class BookmarkFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'file-menu',
            (self.svc, 'bookmark-file-menu.xml'))
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc, 'bookmark-dir-menu.xml'))
        self.subscribe_foreign('window', 'window-config',
            BookmarkWindowConfig)

class BookmarkEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('project', 'project_switched',
                               self.svc.on_project_switched)
        self.subscribe_foreign('buffer', 'document-opened',
                               self.svc.update_document)
        self.subscribe_foreign('buffer', 'document-saved',
                               self.on_document_saved)

    def on_document_saved(self, document=None):
        # we have to save, because we can't detect removed bookmarks yet
        return self.svc.save()


# Service class
class Bookmark(Service, MarkerInterface):
    """Manage bookmarks"""

    actions_config = BookmarkActions
    features_config = BookmarkFeatures
    events_config = BookmarkEvents

    def start(self):
        self._view = BookmarkView(self)
        self._has_loaded = False
        self._items = []
        self._current = None
        self._project = None
        self.load()

    def show_bookmark(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_bookmark(self):
        self.boss.cmd('window', 'remove_view', view=self._view)


    def set_current(self, item):
        self._current = item

    def add_item(self, item):
        for t in self._items:
            if t == item:
                return
        self._items.append(item)
        self._view.add_item(item)
        self.save()

    def list_files(self):
        return self._view._list['file']

    def list_dirs(self):
        return self._view._list['path']

    def remove_current(self):
        if self._current == None:
            return
        self._items.remove(self._current)
        self._view.remove_item(self._current)
        self._current = None
        self.save()

    def bookmark_dir(self, path=None):
        if path == None:
            path = self.boss.cmd('filemanager', 'get_browsed_path')
        source_directory = self.boss.cmd('project', 'get_current_project').source_directory
        title = path
        if title.startswith(source_directory):
            title = title[len(source_directory):]
            if title == '':
                title = _('(project root)')
            else:
                title = '.' + title
        item = BookmarkItemPath(title=title, data=path)
        self.add_item(item)

    def _fill_file(self, filename, line):
        if filename == None:
            document = self.boss.cmd('buffer', 'get_current')
            if document == None:
                return
            filename = document.filename
        if line == None:
            line = self.boss.editor.cmd('get_current_line_number')
        return (filename, line)

    def bookmark_file(self, filename=None, line=None):
        filename, line = self._fill_file(filename, line)
        filename_title = os.path.basename(filename)
        item = BookmarkItemFile(self, data=filename, line=line)
        self.add_item(item)
        self.boss.get_service('editor').emit('marker-changed', marker=item)

    def bookmark_toggle_file(self, filename=None, line=None):
        """
        Add/removed a bookmark depending if there is already one
        """
        filename, line = self._fill_file(filename, line)
        for item in self.list_files():
            if item.data == filename and item.line == line:
                # change the line to -1 and fire the marker-changed so it's 
                # known that the marker will be removed
                item._lineno = -1
                self.boss.get_service('editor'). \
                    emit('marker-changed', marker=item)
                self._items.remove(item)
                self._view.remove_item(item)
                if self._current == item:
                    self._current = None
                break
        else:
            self.bookmark_file(filename, line)

    def update_document(self, document):
        for item in self.list_files():
            if document.filename == item.data:
                self.boss.get_service('editor'). \
                    emit('marker-changed', marker=item)

    def on_project_switched(self, project):
        if project != self._project:
            self._project = project
            self.load()

    def _serialize(self):
        data = {}
        for t in self._items:
            if not data.has_key(t.group):
                data[t.group] = []
            if t.group == 'file':
                if self._project:
                    path = self._project.get_relative_path_for(t.data)
                else:
                    path = None
                if path:
                    path = os.path.sep.join(path)
                else:
                    path = t.data
                data[t.group].append((path, 
                    int(t.line)))
            else:
                data[t.group].append(t.data)
        return data

    def _unserialize(self, data):
        if data == None:
            return
        for key in data:
            items = data[key]
            for item in items:
                if key == 'file':
                    path = os.path.join(self._project.source_directory,  item[0])
                    self.bookmark_file(filename=path, line=item[1])
                elif key == 'path':
                    self.bookmark_dir(path=item)

    def load(self):
        self._items = []
        self._view.clear_all()
        pro = self.boss.cmd('project', 'get_current_project')
        if not pro:
            return
        self._project = pro
        datadir = pro.get_meta_dir('bookmark')
        datafile = os.path.join(datadir, 'bookmark.json')
        if os.path.isfile(datafile):
            try:
                fp = open(datafile, "r")
                data = simplejson.load(fp)
                self._unserialize(data)
            except Exception, e:
                self.log.exception(e)
                return
            
        #self._unserialize(data)

    def save(self):
        data = self._serialize()
        pro = self.boss.cmd('project', 'get_current_project')
        if not pro:
            #FIXME: should we save it in the default settings ?
            return
        else:
            datadir = pro.get_meta_dir('bookmark')
            datafile = os.path.join(datadir, 'bookmark.json')
        try:
            fp = open(datafile, "w")
            simplejson.dump(data, fp, indent=1)
        except Exception, e:
            self.log.exception(e)
            
        #FIXME: reimplement !!!
        #self.boss.cmd('project', 'save_to_current_project',
        #        section_name='bookmark', section_data=data)

    def stop(self):
        if self.get_action('show_bookmark').get_active():
            self.hide_bookmark()

    def _goto(self, direction):
        if not self._view:
            return
        lst = self._view._list['file']
        if not len(lst):
            return
        cur = lst.get_selected()
        if not cur:
            cur = lst.select_paths([0])
            cur = lst.get_selected()
        if direction > 0:
            sel = lst.get_next(cur)
        else:
            sel = lst.get_previous(cur)
        lst.select(sel)
        self.set_current(sel)
        sel.run(self)

    def goto_next(self):
        self._goto(1)
    
    def goto_prev(self):
        self._goto(-1)
        
    def get_line_markers(self, filename):
        for i in self._list['file']:
            if i.data == filename:
                yield i
        

# Required Service attribute for service loading
Service = Bookmark



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
