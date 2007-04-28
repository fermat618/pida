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


import os.path
import time

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView, PidaGladeView

from pida.ui.htmltextview import HtmlTextView

from pida.utils.gthreads import AsyncTask, gcall

try:
    from pygments import highlight
    from pygments.lexers import DiffLexer
    from pygments.formatters import HtmlFormatter
except ImportError:
    highlight = None

class DiffViewer(PidaView):

    icon_name = gtk.STOCK_COPY
    label_text = 'Differences'
    
    def create_ui(self):
        hb = gtk.HBox()
        sb = gtk.ScrolledWindow()
        self._html = HtmlTextView()
        sb.add(self._html)
        hb.pack_start(sb)
        self.add_main_widget(hb)
        hb.show_all()

    def set_diff(self, diff):
        if highlight is None:
            data = '<pre>\n%s</pre>\n' % diff
        else:
            data = highlight(diff, DiffLexer(), HtmlFormatter(noclasses=True))
        self._html.display_html(data)

class VersionControlLog(PidaGladeView):

    gladefile = 'version-control-log'

    icon_name = gtk.STOCK_CONNECT
    label_text = 'Version Control Log'

    def create_ui(self):
        self._buffer = self.log_text.get_buffer()
        self._buffer.create_tag('time', weight=700)
        self._buffer.create_tag('title', foreground='#0000c0', weight=700,
        pixels_below_lines=5)
        self._buffer.create_tag('result')

    def append_entry(self, text, tag):
        self.append(text, tag)
        gcall(self.log_text.scroll_to_iter, self._buffer.get_end_iter(), 0)

    def append_time(self):
        self.append('%s\n' % time.asctime(), 'time')
    
    def append_stock(self, stock_id):
        anchor = self._buffer.create_child_anchor(self._buffer.get_end_iter())
        im = gtk.Image()
        im.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
        im.show()
        self.log_text.add_child_at_anchor(im, anchor)

    def append_action(self, action, stock_id):
        self.svc.ensure_log_visible()
        self.append_stock(stock_id)
        self.append_entry('%s\n' % action, 'title')

    def append_result(self, result):
        self.svc.ensure_log_visible()
        self.append_time()
        self.append_entry('%s\n' % result.strip(), 'result')

    def append(self, text, tag):
        self._buffer.insert_with_tags_by_name(
            self._buffer.get_end_iter(), text, tag)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_vc_log').set_active(False)

class VersioncontrolFeaturesConfig(FeaturesConfig):
    
    def create_features(self):
        self.create_feature("workdir-manager")
    
    def subscribe_foreign_features(self):
        from pida.utils.anyvc import all_known

        for mgr in all_known:
            self.subscribe_feature("workdir-manager", mgr)

        self.subscribe_foreign_feature(
                "filemanager", "file_lister",
                self.svc.list_files
                )
        self.subscribe_foreign_feature(
                "filemanager", "file_hidden_check",
                self.svc.ignored_file_checker
                )
        self.subscribe_foreign_feature('contexts', 'file-menu',
            (self.svc.get_action_group(), 'versioncontrol-file-menu.xml'))
        self.subscribe_foreign_feature('contexts', 'dir-menu',
            (self.svc.get_action_group(), 'versioncontrol-dir-menu.xml'))

class VersionControlEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('buffer', 'document-changed',
            self.svc.on_document_changed)
        self.subscribe_foreign_event('project', 'project_switched',
            self.svc.on_project_changed)


class VersioncontrolCommandsConfig(CommandsConfig):
    
    def get_workdirmanager(self,path):
        return self.svc.get_workdir_manager_for_path(path)

class VersionControlActions(ActionsConfig):

    def create_actions(self):

        self.create_action(
            'show_vc_log',
            TYPE_TOGGLE,
            'Version Control Log',
            'Show the version control log',
            gtk.STOCK_CONNECT,
            self.on_show_vc_log,
            '<Shift><Control>2',
        )

        self.create_action(
            'more_vc_menu',
            TYPE_NORMAL,
            'More Version Control',
            'More Version Control Commands',
            gtk.STOCK_CONNECT,
            lambda *a: None,
            'NOACCEL'
        )

        self.create_action(
            'diff_document',
            TYPE_NORMAL,
            'Differences',
            'Version Control differences for the current document',
            gtk.STOCK_COPY,
            self.on_diff_document,
            '<Shift><Control>d',
        )

        self.create_action(
            'diff_project',
            TYPE_NORMAL,
            'Differences',
            'Get the version control differences for the current project',
            gtk.STOCK_COPY,
            self.on_diff_project,
        )

        self.create_action(
            'diff_for_file',
            TYPE_NORMAL,
            'Differences',
            'Get the version control diff on this file',
            gtk.STOCK_COPY,
            self.on_diff_for_file,
            'NOACCEL',
        )

        self.create_action(
            'diff_for_directory',
            TYPE_NORMAL,
            'Differences',
            'Get the version control diff on this directory',
            gtk.STOCK_COPY,
            self.on_diff_for_dir,
            'NOACCEL',
        )

        self.create_action(
            'commit_document',
            TYPE_NORMAL,
            'Commit',
            'Commit the current document',
            gtk.STOCK_GO_UP,
            self.on_commit_document,
        )

        self.create_action(
            'commit_project',
            TYPE_NORMAL,
            'Commit',
            'Commit the current project',
            gtk.STOCK_GO_UP,
            self.on_commit_project,
        )

        self.create_action(
            'commit_for_file',
            TYPE_NORMAL,
            'Commit',
            'Commit the selected file',
            gtk.STOCK_GO_UP,
            self.on_commit_for_file,
            'NOACCEL'
        )

        self.create_action(
            'commit_for_dir',
            TYPE_NORMAL,
            'Commit',
            'Commit the selected directory',
            gtk.STOCK_GO_UP,
            self.on_commit_for_directory,
            'NOACCEL'
        )

        self.create_action(
            'update_document',
            TYPE_NORMAL,
            'Update',
            'Update the current document',
            gtk.STOCK_GO_DOWN,
            self.on_update_document,
        )

        self.create_action(
            'update_project',
            TYPE_NORMAL,
            'Update',
            'Update the current project',
            gtk.STOCK_GO_DOWN,
            self.on_update_project,
        )

        self.create_action(
            'update_for_file',
            TYPE_NORMAL,
            'Update',
            'Update the selected file',
            gtk.STOCK_GO_DOWN,
            self.on_update_for_file,
            'NOACCEL'
        )

        self.create_action(
            'update_for_dir',
            TYPE_NORMAL,
            'Update',
            'Update the selected file',
            gtk.STOCK_GO_DOWN,
            self.on_update_for_dir,
            'NOACCEL'
        )

        self.create_action(
            'add_document',
            TYPE_NORMAL,
            'Add',
            'Add the current document',
            gtk.STOCK_ADD,
            self.on_add_document,
        )

        self.create_action(
            'add_for_file',
            TYPE_NORMAL,
            'Add',
            'Add the selected file',
            gtk.STOCK_ADD,
            self.on_add_for_file,
            'NOACCEL'
        )

        self.create_action(
            'add_for_dir',
            TYPE_NORMAL,
            'Add',
            'Add the selected file',
            gtk.STOCK_ADD,
            self.on_add_for_dir,
            'NOACCEL'
        )

        self.create_action(
            'remove_document',
            TYPE_NORMAL,
            'Remove',
            'Remove the current document',
            gtk.STOCK_DELETE,
            self.on_remove_document,
            'NOACCEL',
        )

        self.create_action(
            'remove_for_file',
            TYPE_NORMAL,
            'Remove',
            'Remove the selected file',
            gtk.STOCK_DELETE,
            self.on_remove_for_file,
            'NOACCEL',
        )

        self.create_action(
            'remove_for_dir',
            TYPE_NORMAL,
            'Remove',
            'Remove the selected directory',
            gtk.STOCK_DELETE,
            self.on_remove_for_dir,
            'NOACCEL',
        )

        self.create_action(
            'revert_document',
            TYPE_NORMAL,
            'Revert',
            'Revert the current document',
            gtk.STOCK_UNDO,
            self.on_revert_document,
            'NOACCEL'
        )

        self.create_action(
            'revert_project',
            TYPE_NORMAL,
            'Revert',
            'Revert the current project',
            gtk.STOCK_UNDO,
            self.on_revert_project,
            'NOACCEL'
        )

        self.create_action(
            'revert_for_file',
            TYPE_NORMAL,
            'Revert',
            'Revert the selected file',
            gtk.STOCK_UNDO,
            self.on_revert_for_file,
            'NOACCEL'
        )

        self.create_action(
            'revert_for_dir',
            TYPE_NORMAL,
            'Revert',
            'Revert the selected directory',
            gtk.STOCK_UNDO,
            self.on_revert_for_dir,
            'NOACCEL'
        )

    def on_show_vc_log(self, action):
        if action.get_active():
            self.svc.show_log()
        else:
            self.svc.hide_log()

    def on_diff_document(self, action):
        path = self.svc.current_document.filename
        self.svc.diff_path(path)

    def on_diff_project(self, action):
        path = self.svc.current_project.source_directory
        self.svc.diff_path(path)

    def on_diff_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.diff_path(path)

    def on_diff_for_dir(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.diff_path(path)

    def on_commit_document(self, action):
        path = self.svc.current_document.filename
        self.svc.commit_path(path)

    def on_commit_project(self, action):
        path = self.svc.current_project.source_directory
        self.svc.commit_path(path)

    def on_commit_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.commit_path(path)

    def on_commit_for_directory(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.commit_path(path)

    def on_update_document(self, action):
        path = self.svc.current_document.filename
        self.svc.update_path(path)

    def on_update_project(self, action):
        path = self.svc.current_project.source_directory
        self.svc.update_path(path)

    def on_update_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.update_path(path)

    def on_update_for_dir(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.update_path(path)

    def on_add_document(self, action):
        path = self.svc.current_document.filename
        self.svc.add_path(path)

    def on_add_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.add_path(path)

    def on_add_for_dir(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.add_path(path)

    def on_remove_document(self, action):
        path = self.svc.current_document.filename
        self.svc.remove_path(path)

    def on_remove_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.remove_path(path)

    def on_remove_for_dir(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.remove_path(path)

    def on_revert_document(self, action):
        path = self.svc.current_document.filename
        self.svc.revert_path(path)

    def on_revert_project(self, action):
        path = self.svc.current_project.source_directory
        self.svc.revert_path(path)

    def on_revert_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.revert_path(path)

    def on_revert_for_dir(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.revert_path(path)


# Service class
class Versioncontrol(Service):
    """The Versioncontrol service"""

    features_config = VersioncontrolFeaturesConfig
    commands_config = VersioncontrolCommandsConfig
    actions_config = VersionControlActions
    events_config = VersionControlEvents

    def pre_start(self):
        self.on_document_changed(None)
        self.on_project_changed(None)

    def start(self):
        self._log = VersionControlLog(self)
    
    def ignored_file_checker(self, path, name, state):
        return not ( state == "hidden" or state == "ignored")
   
    def get_workdir_manager_for_path(self, path):
        for vcm in self.features("workdir-manager"):
            try:
                return vcm(path) #TODO: this shouldnt need an exception
            except ValueError:
                pass

    def list_files(self, path):
        workdir = self.get_workdir_manager_for_path(path)

        if workdir is not None: 
            for item in workdir.list(paths=[path]):
                abspath = item.abspath
                name = os.path.basename (abspath)
                path = os.path.dirname(abspath)
                yield name, path, item.state

    def diff_path(self, path):
        task = AsyncTask(self._do_diff, self._done_diff)
        task.start(path)

    def _do_diff(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.diff(paths=[path])

    def _done_diff(self, diff):
        view = DiffViewer(self)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=view)
        view.set_diff(diff)

    def update_path(self, path):
        self._log.append_action('Updating: %s' % path, gtk.STOCK_GO_DOWN)
        task = AsyncTask(self._do_update, self._done_update)
        task.start(path)

    def _do_update(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.update(paths=[path])

    def _done_update(self, update):
        self._log.append_result(update)

    def commit_path(self, path, message):
        self._log.append_action('Committing: %s' % path, gtk.STOCK_GO_UP)
        task = AsyncTask(self._do_commit, self._done_commit)
        task.start(path, message)

    def _do_commit(self, path, message):
        vc = self.get_workdir_manager_for_path(path)
        return vc.commit(paths=[path])

    def _done_commit(self, update):
        self._log.append_result(update)

    def revert_path(self, path):
        self._log.append_action('Reverting: %s' % path, gtk.STOCK_UNDO)
        task = AsyncTask(self._do_revert, self._done_revert)
        task.start(path)

    def _do_revert(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.revert(paths=[path])
        
    def _done_revert(self, result):
        self._log.append_result(result)

    def add_path(self, path):
        self._log.append_action('Adding: %s' % path, gtk.STOCK_ADD)
        task = AsyncTask(self._do_add, self._done_add)
        task.start(path)

    def _do_add(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.add(paths=[path])

    def _done_add(self, result):
        self._log.append_result(result)

    def remove_path(self, path):
        self._log.append_action('Removing: %s' % path, gtk.STOCK_REMOVE)
        task = AsyncTask(self._do_remove, self._done_remove)
        task.start(path)

    def _do_remove(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.remove(paths=[path])

    def _done_remove(self, result):
        self._log.append_result(result)

    def on_document_changed(self, document):
        for action in ['diff_document', 'revert_document', 'add_document',
        'remove_document', 'update_document', 'commit_document']:
            self.get_action(action).set_sensitive(document is not None)
        self.current_document = document

    def on_project_changed(self, project):
        for action  in ['diff_project', 'revert_project', 'update_project',
        'commit_project']:
            self.get_action(action).set_sensitive(project is not None)
        self.current_project = project

    def show_log(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._log)

    def hide_log(self):
        self.boss.cmd('window', 'remove_view', view=self._log)

    def ensure_log_visible(self):
        action = self.get_action('show_vc_log')
        if not action.get_active():
            action.set_active(True)
        else:
            self.boss.cmd('window', 'present_view', view=self._log)
        
        



# Required Service attribute for service loading
Service = Versioncontrol



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
