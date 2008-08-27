# -*- coding: utf-8 -*-

# Copyright (c) 2007 Alexander Gabriel

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

# Standard Libs
import os
import gtk

# Moo Imports
import moo

# PIDA Imports
from pida.ui.views import PidaView
from pida.core.editors import EditorService, EditorActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE
from pida.core.environment import pida_home


# locale
from pida.core.locale import Locale
locale = Locale('mooedit')
_ = locale.gettext


class MooeditMain(PidaView):
    """Main Mooedit View.

       This View contains a gtk.Notebook for displaying buffers.
    """

    def create_ui(self):
        self._embed = MooeditEmbed(self)
        self.add_main_widget(self._embed)

    #AA Needs implementing
    #EA really? I didn't see it called anytime.
    #   Did it with relay to the service for now.
    def grab_input_focus(self):
        print "\n\ngrab_input_focus\n\n"
        self.svc.grab_focus()
        pass


class MooeditPreferences(PidaView):
    """Mooedit Preferences View.

       Here the Mooedit editor preferences dialog is included
       and provided with some buttons.
    """

    label_text = _('Mooedit Preferences')

    icon_name = 'package_utilities'

    def create_ui(self):
        prefs = self.svc._editor_instance.prefs_page()
        prefs.emit('init')
        prefs.show()
        vbox = gtk.VBox()
        vbox.pack_start(prefs)
        self._prefs = prefs

        bb = gtk.HButtonBox()

        bb.set_spacing(6)
        bb.set_layout(gtk.BUTTONBOX_END)

        self._apply_but = gtk.Button(stock=gtk.STOCK_APPLY)
        self._apply_but.connect('clicked', self.cb_apply_button_clicked)

        self._ok_but = gtk.Button(stock=gtk.STOCK_OK)
        self._ok_but.connect('clicked', self.cb_ok_button_clicked)

        self._cancel_but = gtk.Button(stock=gtk.STOCK_CANCEL)
        self._cancel_but.connect('clicked', self.cb_cancel_button_clicked)

        bb.pack_start(self._apply_but)
        bb.pack_start(self._cancel_but)
        bb.pack_start(self._ok_but)
        bb.show_all()
        vbox.pack_start(bb)
        vbox.show()
        self.add_main_widget(vbox)

    def cb_ok_button_clicked(self, button):
        self._apply()
        self.svc.show_preferences(self.svc.get_action('mooedit_preferences').set_active(False))

    def cb_apply_button_clicked(self, button):
        self._apply()

    def cb_cancel_button_clicked(self, button):
        self.svc.show_preferences(self.svc.get_action('mooedit_preferences').set_active(False))

    def _apply(self):
        self._prefs.emit('apply')
        self.svc.save_moo_state()

    def can_be_closed(self):
        self.svc.get_action('mooedit_preferences').set_active(False)


class MooeditEmbed(gtk.Notebook):
    """Mooedit Embed

       This is the actual Notebook that holds our buffers.
    """

    def __init__(self, mooedit):
        gtk.Notebook.__init__(self)
        self.set_scrollable(True)
        self._mooedit = mooedit
        self.show_all()

    def _create_tab(self, editor):
        hb = gtk.HBox(spacing=2)
        if editor.get_filename():
            fn = os.path.split(editor.get_filename())[1]
        else:
            fn = _("New Document")
        editor._label = gtk.Label()
        editor._label.set_text(fn)
        b = gtk.Button()
        b.set_border_width(0)
        b.connect("clicked", self._close_cb, editor)
        b.set_relief(gtk.RELIEF_NONE)
        b.set_size_request(20, 20)
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        b.add(img)
        vb = gtk.VBox()
        vb.pack_start(gtk.Alignment())
        vb.pack_start(b, expand=False)
        vb.pack_start(gtk.Alignment())
        hb.pack_start(editor._label)
        hb.pack_start(vb, expand=False)
        hb.show_all()
        return hb

    def _close_cb(self, btn, editor):
        self._mooedit.svc.boss.get_service('buffer').cmd('close_file', file_name=editor.get_filename())


class MooeditView(gtk.ScrolledWindow):
    """Mooedit View

       A gtk.ScrolledWindow containing the editor instance we get from mooedit.
    """

    def __init__(self, document):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.editor = document.editor
        self.document = document
        self.add(document.editor)
        self.show_all()


class MooeditActionsConfig(EditorActionsConfig):
    """Mooedit Actions Config

       This defines some menu items for the edit menu.
    """

    def create_actions(self):
        EditorActionsConfig.create_actions(self)
        self.create_action(
            'mooedit_save_as',
            TYPE_NORMAL,
            _('Save as'),
            _('Save file as'),
            gtk.STOCK_SAVE_AS,
            self.on_save_as,
            '<Shift><Control>S'
        )
        self.create_action(
            'mooedit_preferences',
            TYPE_TOGGLE,
            _('Edit Mooedit Preferences'),
            _('Show the editors preferences dialog'),
            gtk.STOCK_PREFERENCES,
            self.on_project_preferences,
        )
        self.create_action(
            'mooedit_find',
            TYPE_NORMAL,
            _('Find in buffer'),
            _('Find'),
            gtk.STOCK_FIND,
            self.on_find,
            '<Control>F'
        )
        self.create_action(
            'mooedit_find_next',
            TYPE_NORMAL,
            _('Find next in buffer'),
            _(''),
            gtk.STOCK_GO_FORWARD,
            self.on_find_next,
            'F3',
        )
        self.create_action(
            'mooedit_find_prev',
            TYPE_NORMAL,
            _('Find previous in buffer'),
            _(''),
            gtk.STOCK_GO_BACK,
            self.on_find_prev,
            '<Shift>F3',
        )
        self.create_action(
            'mooedit_replace',
            TYPE_NORMAL,
            _('Find and replace'),
            _('Find & replace'),
            gtk.STOCK_FIND_AND_REPLACE,
            self.on_replace,
            '<Control>R',
        )
        self.create_action(
            'mooedit_find_word_next',
            TYPE_NORMAL,
            _('Find current word down'),
            _(''),
            gtk.STOCK_GO_BACK,
            self.on_find_word_next,
            'F4',
        )
        self.create_action(
            'mooedit_find_word_prev',
            TYPE_NORMAL,
            _('Find current word up'),
            _(''),
            gtk.STOCK_GO_FORWARD,
            self.on_find_word_prev,
            '<Shift>F4',
        )
        self.create_action(
            'mooedit_goto',
            TYPE_NORMAL,
            _('Goto line'),
            _('Goto line'),
            gtk.STOCK_GO_DOWN,
            self.on_goto,
            '<Control>G',
        )

    def on_project_preferences(self, action):
        self.svc.show_preferences(action.get_active())

    def on_save_as(self, action):
        self.svc._current.editor.save_as()

    def on_find(self, action):
        self.svc._current.editor.emit('find-interactive')

    def on_find_next(self, action):
        self.svc._current.editor.emit('find-next-interactive')

    def on_find_prev(self, action):
        self.svc._current.editor.emit('find-prev-interactive')

    def on_replace(self, action):
        self.svc._current.editor.emit('replace-interactive')

    def on_find_word_next(self, action):
        self.svc._current.editor.emit('find-word-at-cursor', True)

    def on_find_word_prev(self, action):
        self.svc._current.editor.emit('find-word-at-cursor', False)

    def on_goto(self, action):
        self.svc._current.editor.emit('goto-line-interactive')


# Service class
class Mooedit(EditorService):
    """Moo Editor Interface for PIDA

       Let's you enjoy all the GUI love from mooedit with all the superb IDE
       features PIDA has to offer. Use with caution, may lead to addiction.
    """

    actions_config = MooeditActionsConfig
    
    def pre_start(self):
        # mooedit is able to open empty documents
        self.features.publish('new_file')
        
        try:
            self.script_path = os.path.join(pida_home, 'pida_mooedit.rc')
            self._state_path = os.path.join(pida_home, 'pida_mooedit.state')
            moo.utils.prefs_load(sys_files=None, file_rc=self.script_path, file_state=self._state_path)
            self._editor_instance = moo.edit.create_editor_instance()
            moo.edit.plugin_read_dirs()
            self._documents = {}
            self._current = None
            self._main = MooeditMain(self)
            self._preferences = MooeditPreferences(self)
            self._embed = self._main._embed
            self._embed.connect("switch-page", self._changed_page)
            self._embed.connect("drag_drop", self._drag_drop_cb)
            self._embed.connect("drag_motion", self._drag_motion_cb)
            self._embed.connect ("drag_data_received", self._drag_data_recv)
            self._embed.drag_dest_set(0, [
                                    ("GTK_NOTEBOOK_TAB", gtk.TARGET_SAME_APP, 1),
                                    ("text/uri-list", 0, 2)],
                                    gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
            self.boss.cmd('window', 'add_view', paned='Editor', view=self._main)
            self.boss.get_service('editor').emit('started')
            return True
        except Exception, err:
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        self.update_actions(enabled=False)
        return True

    def save_moo_state(self):
        moo.utils.prefs_save(self.script_path, self._state_path)

    def show_preferences(self, visible):
        if visible:
            self.boss.cmd('window', 'add_view', paned='Plugin',
                          view=self._preferences)
        else:
            self.boss.cmd('window', 'remove_view',
                          view=self._preferences)

    def stop(self):
        views = [view for view in self._documents.values()]
        close = True
        for view in views:
            editor_close = view.editor.close()
            self._embed.remove_page(self._embed.page_num(view))
            close = close & editor_close
        self.boss.stop(force=True)
        return close

    def update_actions(self, enabled=True):
        all = True
        if not enabled:
            all = False
        self.get_action('save').set_sensitive(all)
        self.get_action('mooedit_save_as').set_sensitive(all)
        self.get_action('cut').set_sensitive(all)
        self.get_action('copy').set_sensitive(all)
        self.get_action('paste').set_sensitive(all)
        if enabled and self._current and self._current.editor:
            self.get_action('undo').set_sensitive(self._current.editor.can_undo())
            self.get_action('redo').set_sensitive(self._current.editor.can_redo())
        else:
            self.get_action('undo').set_sensitive(all)
            self.get_action('redo').set_sensitive(all)
        self.get_action('focus_editor').set_sensitive(all)
        self.get_action('mooedit_goto').set_sensitive(all)
        self.get_action('mooedit_find').set_sensitive(all)
        self.get_action('mooedit_find_next').set_sensitive(all)
        self.get_action('mooedit_find_prev').set_sensitive(all)
        self.get_action('mooedit_find_word_next').set_sensitive(all)
        self.get_action('mooedit_find_word_prev').set_sensitive(all)
        self.get_action('mooedit_replace').set_sensitive(all)
        

    def open(self, document):
        """Open a document"""
        if document.unique_id not in self._documents.keys():
            if self._load_file(document):
                self._embed.set_current_page(-1)
                if self._embed.get_n_pages() == 1:
                    self.update_actions()
                    if document.is_new:
                        self.get_action('save').set_sensitive(True)
                    else:
                        self.get_action('save').set_sensitive(False)
        else:
            #EA: the file was already open. we switch to it.
            self._embed.set_current_page(self._embed.page_num(self._documents[document.unique_id]))
            self.update_actions()

    def open_list(self, documents):
        for doc in documents:
            self._load_file(doc)

    def close(self, document):
        """Close a document"""
        closing = self._documents[document.unique_id].editor.close()
        if closing:
            self._embed.remove_page(self._embed.page_num(self._documents[document.unique_id]))
            del self._documents[document.unique_id]
            if self._embed.get_n_pages() == 0:
                self.update_actions(enabled=False)
        return closing

    def save(self):
        """Save the current document"""
        self._current.editor.save()
        self.boss.cmd('buffer', 'current_file_saved')

    def save_as(self):
        """Save the current document"""
        self._current.editor.save_as()
        self.boss.cmd('buffer', 'current_file_saved')

    def cut(self):
        """Cut to the clipboard"""
        self._current.editor.emit('cut-clipboard')

    def copy(self):
        """Copy to the clipboard"""
        self._current.editor.emit('copy-clipboard')

    def paste(self):
        """Paste from the clipboard"""
        self._current.editor.emit('paste-clipboard')

    def undo(self):
        self._current.editor.undo()
        self.get_action('redo').set_sensitive(True)
        if not self._current.editor.can_undo():
            self.get_action('undo').set_sensitive(False)

    def redo(self):
        self._current.editor.redo()
        self.get_action('undo').set_sensitive(True)
        if not self._current.editor.can_redo():
            self.get_action('redo').set_sensitive(False)

    def goto_line(self, line):
        """Goto a line"""
        self._current.editor.move_cursor(line-1, 0, False, True)

    def set_path(self, path):
        pass

    def grab_focus(self):
        if self._current is not None:
            self._current.editor.grab_focus()

    def _changed_page(self, notebook, page, page_num):
        self._current = self._embed.get_nth_page(page_num)
        self.boss.cmd('buffer', 'open_file', file_name=self._current.editor.get_filename())

    def _load_file(self, document):
        try:
            if document is None:
                editor = self._editor_instance.new_doc()
            else:
                editor = self._editor_instance.create_doc(document.filename)
            document.editor = editor
            view = MooeditView(document)
            view._star = False
            view._exclam = False
            document.editor.connect("doc_status_changed", self._buffer_changed, view)
            document.editor.connect("filename-changed", self._buffer_renamed, view)
            label = self._embed._create_tab(document.editor)
            self._documents[document.unique_id] = view
            self._embed.append_page(view, label)
            self._embed.set_tab_reorderable(view, True)
            #self._embed.set_tab_detachable(view, True)
            self._current = view
            return True
        except Exception, err:
            self.log.exception(err)
            return False

    def _buffer_changed(self, buffer, view):
        status = view.editor.get_status()
        if moo.edit.EDIT_MODIFIED & status == moo.edit.EDIT_MODIFIED:
            if not self._current.editor.can_redo():
                self.get_action('redo').set_sensitive(False)
            if not view._star:
                s = view.editor._label.get_text()
                if view._exclam:
                    s = s[1:]
                    view._exclam = False
                view.editor._label.set_text("*" + s)
                view._star = True
                self.get_action('undo').set_sensitive(True)
        if moo.edit.EDIT_CLEAN & status == moo.edit.EDIT_CLEAN:
            #print "clean"
            pass
        if moo.edit.EDIT_NEW & status == moo.edit.EDIT_NEW:
            #print "new"
            pass
        if moo.edit.EDIT_CHANGED_ON_DISK & status == moo.edit.EDIT_CHANGED_ON_DISK:
            if not view._exclam:
                s = view.editor._label.get_text()
                if view._star:
                    s = s[1:]
                    view._star = False
                view.editor._label.set_text("!" + s)
                view._exclam = True
        if status == 0:
            if view._star or view._exclam:
                s = view.editor._label.get_text()
                s = s[1:]
                view._exclam = False
                view._star = False
                view.editor._label.set_text(s)

    def _buffer_modified(self, buffer, view):
        s = view.editor._label.get_text()
        view.editor._label.set_text("*" + s)

    def _buffer_renamed(self, buffer, new_name, view):
        view.editor._label.set_text(new_name)
        view.document.filename = new_name

    def _drag_motion_cb (self, widget, context, x, y, time):
        list = widget.drag_dest_get_target_list()
        target = widget.drag_dest_find_target(context, list)

        if target is None:
            return False
        else:
            if target == "text/uri-list":
                context.drag_status(gtk.gdk.ACTION_COPY, time)
            else:
                widget.drag_get_data(context, "GTK_NOTEBOOK_TAB", time)
            return True

    def _drag_drop_cb (self, widget, context, x, y, time):
        list = widget.drag_dest_get_target_list()
        target = widget.drag_dest_find_target (context, list);

        if (target == "text/uri-list"):
            widget.drag_get_data (context, "text/uri-list", time)
        else:
            context.finish (False, False, time)
        return True

    def _drag_data_recv(self, widget, context, x, y, selection, targetType, time):
        if targetType == 2:
            for filename in selection.get_uris():
                widget._mooedit.svc.boss.cmd('buffer', 'open_file', file_name=filename[7:])
            return True
        else:
            return False


# Required Service attribute for service loading
Service = Mooedit



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

