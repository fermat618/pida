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
from cgi import escape

import gtk, pango

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView, PidaGladeView

from pida.ui.htmltextview import HtmlTextView
from pida.ui.buttons import create_mini_button

from pida.utils.gthreads import AsyncTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('versioncontrol')
_ = locale.gettext

try:
    from pygments import highlight
    from pygments.lexers import DiffLexer
    from pygments.formatters import HtmlFormatter
except ImportError:
    highlight = None

class DiffViewer(PidaView):

    icon_name = gtk.STOCK_COPY
    label_text = _('Differences')
    
    def create_ui(self):
        hb = gtk.HBox()
        self.add_main_widget(hb)
        sb = gtk.ScrolledWindow()
        sb.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sb.set_shadow_type(gtk.SHADOW_IN)
        sb.set_border_width(3)
        self._html = HtmlTextView()
        self._html.set_left_margin(6)
        self._html.set_right_margin(6)
        sb.add(self._html)
        hb.pack_start(sb)
        vb = gtk.VBox()
        hb.pack_start(vb, expand=False)
        self._close_button = create_mini_button(gtk.STOCK_CLOSE,
            'Close the diff viewer', self.on_close_button_clicked)
        vb.pack_start(self._close_button, expand=False)
        hb.show_all()

    def set_diff(self, diff):
        if highlight is None:
            data = '<pre>\n%s</pre>\n' % diff
        else:
            data = highlight(diff, DiffLexer(), HtmlFormatter(noclasses=True))
        self._html.display_html(data)

    def on_close_button_clicked(self, button):
        self.svc.boss.cmd('window', 'remove_view', view=self)

class VersionControlLog(PidaGladeView):

    gladefile = 'version-control-log'

    icon_name = gtk.STOCK_CONNECT
    label_text = _('Version Control Log')

    def create_ui(self):
        self._buffer = self.log_text.get_buffer()
        self._buffer.create_tag('time', foreground='#0000c0')
        self._buffer.create_tag('argument', weight=700)
        self._buffer.create_tag('title', style=pango.STYLE_ITALIC)
        self._buffer.create_tag('result', font='Monospace')
        self.append_time()
        self.append_stock(gtk.STOCK_CONNECT)
        self.append(_(' Version Control Log Started\n\n'), 'argument')

    def append_entry(self, text, tag):
        self.append(text, tag)

    def append_time(self):
        self.append('%s\n' % time.asctime(), 'time')
    
    def append_stock(self, stock_id):
        anchor = self._buffer.create_child_anchor(self._buffer.get_end_iter())
        im = gtk.Image()
        im.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
        im.show()
        self.log_text.add_child_at_anchor(im, anchor)

    def append_action(self, action, argument, stock_id):
        self.append_time()
        self.append_stock(stock_id)
        self.append_entry(' %s: ' % action, 'title')
        self.append_entry('%s\n' % argument, 'argument')

    def append_result(self, result):
        self.append_entry('%s\n\n' % result.strip(), 'result')

    def append(self, text, tag):
        self._buffer.insert_with_tags_by_name(
            self._buffer.get_end_iter(), text, tag)
        gcall(self.log_text.scroll_to_iter, self._buffer.get_end_iter(), 0)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_vc_log').set_active(False)

class CommitViewer(PidaGladeView):

    gladefile = 'commit-dialog'
    
    icon_name = gtk.STOCK_GO_UP
    label_text = _('Commit')

    def create_ui(self):
        self._buffer = self.commit_text.get_buffer()
        self._history_index = 0
        self._history = []
        self._path = None

    def _update_view(self):
        self.ok_button.set_sensitive(self._path is not None)
        self.prev_button.set_sensitive(self._history_index != 0)
        self.next_button.set_sensitive(self._history_index !=
                                       len(self._history))
        self.new_button.set_sensitive(self._history_index !=
                                       len(self._history))

    def set_path(self, path):
        self._path = path
        self._update_view()
        self._set_path_label()

    def get_message(self):
        return self._buffer.get_text(self._buffer.get_start_iter(),
                                     self._buffer.get_end_iter())

    def _set_path_label(self):
        if self._path is not None:
            self.path_label.set_markup('<tt><b>%s</b></tt>' %
                                       escape(self._path))
        else:
            self.path_label.set_text('')

    def _commit(self, msg):
        self._history.append(msg)
        self._history_index = len(self._history)
        self._clear_text()
        self._update_view()
        self.svc.commit_path(self._path, msg)
        self.close()

    def _clear_text(self):
        self._buffer.set_text('')

    def _show_history(self):
        if self._history_index == len(self._history):
            self._clear_text()
        else:
            self._buffer.set_text(self._history[self._history_index])
        self.commit_text.grab_focus()
        self._update_view()

    def on_ok_button__clicked(self, button):
        msg = self.get_message().strip()
        if not msg:
            self.svc.error_dlg(_('No Commit Message.'))
        else:
            self._commit(msg)

    def on_close_button__clicked(self, button):
        self.close()

    def on_prev_button__clicked(self, button):
        self._history_index -= 1
        self._show_history()

    def on_next_button__clicked(self, button):
        self._history_index += 1
        self._show_history()

    def on_new_button__clicked(self, button):
        self._history_index = len(self._history)
        self._show_history()

    def on_diff_button__clicked(self, button):
        self.svc.diff_path(self._path)

    def close(self):
        self.set_path(None)
        self.svc.get_action('show_commit').set_active(False)


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
            _('Version Control Log'),
            _('Show the version control log'),
            gtk.STOCK_CONNECT,
            self.on_show_vc_log,
            '<Shift><Control>2',
        )

        self.create_action(
            'show_commit',
            TYPE_TOGGLE,
            _('Commit Message'),
            _('Show the commit message'),
            gtk.STOCK_GO_UP,
            self.on_show_commit,
            'NOACCEL'
        )

        self.create_action(
            'more_vc_menu',
            TYPE_NORMAL,
            _('More Version Control'),
            _('More Version Control Commands'),
            gtk.STOCK_CONNECT,
            lambda *a: None,
            'NOACCEL'
        )

        self.create_action(
            'diff_document',
            TYPE_NORMAL,
            _('Differences'),
            _('Version Control differences for the current document'),
            gtk.STOCK_COPY,
            self.on_diff_document,
            '<Shift><Control>d',
        )

        self.create_action(
            'diff_project',
            TYPE_NORMAL,
            _('Differences'),
            _('Get the version control differences for the current project'),
            gtk.STOCK_COPY,
            self.on_diff_project,
        )

        self.create_action(
            'diff_for_file',
            TYPE_NORMAL,
            _('Differences'),
            _('Get the version control diff on this file'),
            gtk.STOCK_COPY,
            self.on_diff_for_file,
            'NOACCEL',
        )

        self.create_action(
            'diff_for_directory',
            TYPE_NORMAL,
            _('Differences'),
            _('Get the version control diff on this directory'),
            gtk.STOCK_COPY,
            self.on_diff_for_dir,
            'NOACCEL',
        )

        self.create_action(
            'commit_document',
            TYPE_NORMAL,
            _('Commit'),
            _('Commit the current document'),
            gtk.STOCK_GO_UP,
            self.on_commit_document,
        )

        self.create_action(
            'commit_project',
            TYPE_NORMAL,
            _('Commit'),
            _('Commit the current project'),
            gtk.STOCK_GO_UP,
            self.on_commit_project,
        )

        self.create_action(
            'commit_for_file',
            TYPE_NORMAL,
            _('Commit'),
            _('Commit the selected file'),
            gtk.STOCK_GO_UP,
            self.on_commit_for_file,
            'NOACCEL'
        )

        self.create_action(
            'commit_for_dir',
            TYPE_NORMAL,
            _('Commit'),
            _('Commit the selected directory'),
            gtk.STOCK_GO_UP,
            self.on_commit_for_directory,
            'NOACCEL'
        )

        self.create_action(
            'update_document',
            TYPE_NORMAL,
            _('Update'),
            _('Update the current document'),
            gtk.STOCK_GO_DOWN,
            self.on_update_document,
        )

        self.create_action(
            'update_project',
            TYPE_NORMAL,
            _('Update'),
            _('Update the current project'),
            gtk.STOCK_GO_DOWN,
            self.on_update_project,
        )

        self.create_action(
            'update_for_file',
            TYPE_NORMAL,
            _('Update'),
            _('Update the selected file'),
            gtk.STOCK_GO_DOWN,
            self.on_update_for_file,
            'NOACCEL'
        )

        self.create_action(
            'update_for_dir',
            TYPE_NORMAL,
            _('Update'),
            _('Update the selected file'),
            gtk.STOCK_GO_DOWN,
            self.on_update_for_dir,
            'NOACCEL'
        )

        self.create_action(
            'add_document',
            TYPE_NORMAL,
            _('Add'),
            _('Add the current document'),
            gtk.STOCK_ADD,
            self.on_add_document,
        )

        self.create_action(
            'add_for_file',
            TYPE_NORMAL,
            _('Add'),
            _('Add the selected file'),
            gtk.STOCK_ADD,
            self.on_add_for_file,
            'NOACCEL'
        )

        self.create_action(
            'add_for_dir',
            TYPE_NORMAL,
            _('Add'),
            _('Add the selected file'),
            gtk.STOCK_ADD,
            self.on_add_for_dir,
            'NOACCEL'
        )

        self.create_action(
            'remove_document',
            TYPE_NORMAL,
            _('Remove'),
            _('Remove the current document'),
            gtk.STOCK_DELETE,
            self.on_remove_document,
            'NOACCEL',
        )

        self.create_action(
            'remove_for_file',
            TYPE_NORMAL,
            _('Remove'),
            _('Remove the selected file'),
            gtk.STOCK_DELETE,
            self.on_remove_for_file,
            'NOACCEL',
        )

        self.create_action(
            'remove_for_dir',
            TYPE_NORMAL,
            _('Remove'),
            _('Remove the selected directory'),
            gtk.STOCK_DELETE,
            self.on_remove_for_dir,
            'NOACCEL',
        )

        self.create_action(
            'revert_document',
            TYPE_NORMAL,
            _('Revert'),
            _('Revert the current document'),
            gtk.STOCK_UNDO,
            self.on_revert_document,
            'NOACCEL'
        )

        self.create_action(
            'revert_project',
            TYPE_NORMAL,
            _('Revert'),
            _('Revert the current project'),
            gtk.STOCK_UNDO,
            self.on_revert_project,
            'NOACCEL'
        )

        self.create_action(
            'revert_for_file',
            TYPE_NORMAL,
            _('Revert'),
            _('Revert the selected file'),
            gtk.STOCK_UNDO,
            self.on_revert_for_file,
            'NOACCEL'
        )

        self.create_action(
            'revert_for_dir',
            TYPE_NORMAL,
            _('Revert'),
            _('Revert the selected directory'),
            gtk.STOCK_UNDO,
            self.on_revert_for_dir,
            'NOACCEL'
        )

    def on_show_vc_log(self, action):
        if action.get_active():
            self.svc.show_log()
        else:
            self.svc.hide_log()

    def on_show_commit(self, action):
        if action.get_active():
            self.svc.show_commit()
        else:
            self.svc.hide_commit()

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
        self.svc.commit_path_dialog(path)

    def on_commit_project(self, action):
        path = self.svc.current_project.source_directory
        self.svc.commit_path_dialog(path)

    def on_commit_for_file(self, action):
        path = action.contexts_kw['file_name']
        self.svc.commit_path_dialog(path)

    def on_commit_for_directory(self, action):
        path = action.contexts_kw['dir_name']
        self.svc.commit_path_dialog(path)

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
        self._commit = CommitViewer(self)
    
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
            for item in workdir.list(paths=[path], recursive=False):
                abspath = item.abspath
                name = os.path.basename (abspath)
                path = os.path.dirname(abspath)
                yield name, path, item.state

    def diff_path(self, path):
        self._log.append_action('Diffing', path, gtk.STOCK_COPY)
        task = AsyncTask(self._do_diff, self._done_diff)
        task.start(path)

    def _do_diff(self, path):
        vc = self.get_workdir_manager_for_path(path)
        return vc.diff(paths=[path])

    def _done_diff(self, diff):
        view = DiffViewer(self)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=view)
        view.set_diff(diff)

    def execute(self, action, path, stock_id, **kw):
        vc = self.get_workdir_manager_for_path(path)
        commandargs = [vc.cmd] + getattr(vc, 'get_%s_args' % action)(paths=[path], **kw)
        self._log.append_action(action.capitalize(), path, stock_id)
        self.boss.cmd('commander', 'execute', commandargs=commandargs,
                      cwd=vc.base_path, eof_handler=self._executed,
                      use_python_fork=True)

    def _executed(self, term):
        self._log.append_result(term.get_all_text())
        self.boss.cmd('window', 'remove_view', view=term.parent_view)
        self.ensure_log_visible()

    def update_path(self, path):
        self.execute('update', path, gtk.STOCK_GO_DOWN)

    def commit_path(self, path, message=None):
        self.execute('commit', path, gtk.STOCK_GO_UP, message=message)

    def commit_path_dialog(self, path):
        self._commit.set_path(path)
        self.ensure_commit_visible()

    def revert_path(self, path):
        self.execute('revert', path, gtk.STOCK_UNDO)

    def add_path(self, path):
        self.execute('add', path, gtk.STOCK_ADD)

    def remove_path(self, path):
        self.execute('remove', path, gtk.STOCK_REMOVE)

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

    def show_commit(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._commit)

    def hide_commit(self):
        self.boss.cmd('window', 'remove_view', view=self._commit)

    def ensure_commit_visible(self):
        action = self.get_action('show_commit')
        if not action.get_active():
            action.set_active(True)
        else:
            self.boss.cmd('window', 'present_view', view=self._commit)
        
        



# Required Service attribute for service loading
Service = Versioncontrol



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
