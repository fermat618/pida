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


import os, xmlrpclib, base64

import gtk, gobject



# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE
from pida.ui.views import PidaGladeView
from pida.utils.path import walktree
from pida.utils.gthreads import GeneratorTask, AsyncTask
from pida.utils.configobj import ConfigObj

from kiwi.ui.objectlist import Column


# locale
from pida.core.locale import Locale
locale = Locale('snippets')
_ = locale.gettext

RPC_URL = 'http://pida.co.uk/RPC2'

server_proxy = xmlrpclib.ServerProxy(RPC_URL)


def get_value(tab, key):
    if not tab.has_key(key):
        return ''
    return tab[key]


class SnippetsManagerView(PidaGladeView):

    gladefile = 'snippets-manager'
    locale = locale
    label_text = _('Snippets manager')
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self._current = None
        self.item = None
        self.installed_list.set_columns([
            Column('title', title=_('Snippets'), sorted=True, data_type=str,
                expand=True)
            ])
        self.available_list.set_columns([
            Column('title', title=_('Snippets'), sorted=True, data_type=str,
                expand=True)
            ])

    def can_be_closed(self):
        self.svc.get_action('show_snippets').set_active(False)

    def clear_installed(self):
        self.installed_list.clear()

    def add_installed(self, item):
        self.installed_list.append(item)

    def clear_available(self):
        self.available_list.clear()

    def add_available(self, item):
        self.available_list.append(item)

    def on_installed_list__selection_changed(self, ol, item):
        self.installed_information_label.set_text(item.name)

    def on_available_refresh__clicked(self, button):
        self.svc.get_available_snippets()


class SnippetWindow(gtk.Window):

    def __init__(self, snippet, response_callback):
        gtk.Window.__init__(self)
        self.response_callback = response_callback
        self.set_decorated(False)
        self.add_events(gtk.gdk.FOCUS_CHANGE_MASK)
        #self.connect('set-focus-child', self.on_focus_child)
        self.connect('focus-out-event', self.focus_out)
        self._focused = False
        self._vars = {}
        self._create_ui()
        self._vals = {}
        self._valids = {}
        self._snippet = snippet
        self.set_title_label(self._snippet.title)
        self._create_entries()

    def _create_ui(self):
        self._frame = gtk.Frame()
        self.add(self._frame)
        self._frame.set_border_width(6)
        hb = gtk.HBox(spacing=6)
        hb.set_border_width(6)
        self._frame.add(hb)
        vb = gtk.VBox()
        hb.pack_start(vb, expand=False)
        vb.pack_start(self._create_labels(), expand=False)
        vb.pack_start(self._create_entries_box(), expand=False)
        hb.pack_start(self._create_preview_pane(), expand=False)

    def _create_entries(self):
        for variable in self._snippet.variables:
            self._vars[variable.name] = variable
            self.add_entry(variable)
        self.preview()


    def _create_labels(self):
        vb = gtk.VBox()
        self._primary_label = gtk.Label()
        vb.pack_start(self._primary_label, expand=False)
        return vb

    def _create_preview_pane(self):
        self._preview_text = gtk.TextView()
        self._preview_text.set_left_margin(6)
        self._preview_text.set_right_margin(6)
        self._preview_text.set_cursor_visible(False)
        self._preview_text.set_editable(False)
        #self._preview_text.set_app_paintable(True)
        #self._preview_text.connect('expose-event', self._on_preview_text_expose_event)
        #w = gtk.Window()
        #w.set_name('gtk-tooltips')
        #self._ttstyle = w.style
        #self._preview_text.modify_base(gtk.STATE_NORMAL,
        #self._ttstyle.base[gtk.STATE_NORMAL])
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self._preview_text)
        sw.set_size_request(200, -1)
        return sw

    def _create_entries_box(self):
        self._entries = {}
        self._entries_order = []
        self._entries_vb = gtk.VBox(spacing=6)
        self._label_sizer = gtk.SizeGroup(gtk.ORIENTATION_HORIZONTAL)
        return self._entries_vb

    def add_entry(self, variable):
        name = variable.name
        label_text = variable.label
        default = variable.default
        hb = gtk.HBox(spacing=6)
        label = gtk.Label()
        label.set_text(label_text)
        label.set_alignment(1, 0.5)
        self._label_sizer.add_widget(label)
        hb.pack_start(label)
        self._valids[name] = gtk.Image()
        entry = gtk.Entry()
        entry.set_text(default)
        self.validate(entry, name)
        entry.connect('changed', self.on_entry_changed, name)
        self._vals[name] = default
        hb.pack_start(entry, expand=False)
        hb.pack_start(self._valids[name], expand=False)
        self._entries_vb.pack_start(hb, expand=False)
        self._entries[name] = entry
        self._entries_order.append(entry)
        entry.connect('key-press-event', self.on_entry_keypress, name)

    def grab_entry(self):
        self._entry.grab_focus()

    def set_title_label(self, value):
        self._frame.set_label(value)

    def set_primary_label(self, value):
        self._primary_label.set_text(value)

    def set_secondary_label(self, value):
        self._secondary_label.set_text(value)

    def on_entry_changed(self, entry, name):
        self._vals[name] = entry.get_text()
        self.validate(entry, name)
        self.preview()

    def validate(self, entry, name):
        if self._vars[name].required:
            if entry.get_text():
                self._valids[name].set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
            else:
                self._valids[name].set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
        else:
            self._valids[name].set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)

    def preview(self):
        self._preview_text.get_buffer().set_text(self.get_substituted_text())

    def get_substituted_text(self):
        return self._snippet.substitute(self._vals)

    def on_entry_keypress(self, entry, event, name):
        #print name, [event.keyval, event.state, event.string]
        if event.string == '\r':
            if event.state & gtk.gdk.CONTROL_MASK:
                self.respond_success()
            else:
                index = self._entries_order.index(entry)
                if index == len(self._entries_order) - 1:
                    self.respond_success()
                else:
                    self._entries_order[index + 1].grab_focus()
        elif event.string == '\x1b':
            self.respond_failure()
            

    def _on_preview_text_expose_event(self, textview, event):
        #self._ttstyle.attach(self._preview_text.get_window(gtk.TEXT_WINDOW_TEXT))
        textview.style.paint_flat_box(textview.get_window(gtk.TEXT_WINDOW_TEXT),
                                    gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                                    None, textview, "tooltip",
                                    0, 0, -1, -1)
        #self._ttstyle.apply_default_background(self._preview_text.get_window(gtk.TEXT_WINDOW_TEXT),
        #    True, gtk.STATE_NORMAL, None, 0, 0, -1, -1)
        #self._ttstyle.set_background(self._preview_text.get_window(gtk.TEXT_WINDOW_TEXT),
        #    gtk.STATE_NORMAL)

        return False

    def focus_out(self, window, event):
        self.respond_failure()

    def close(self):
        self.hide_all()
        self.destroy()

    def respond_success(self):
        self.response_callback(True, self.get_substituted_text())
        self.close()

    def respond_failure(self):
        self.response_callback(False, None)
        self.close()


class MissingSnippetMetadata(Exception):
    """The template had missing metadata"""


class SnippetVariable(object):

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.label = config['label']
        self.default = config['default']
        self.required = config.as_bool('required')

class BaseSnippet(object):
    
    def __init__(self, snippet_meta):
        self.meta = snippet_meta
        self.name = self.meta.name
        self.title = self.meta.title
        self.variables = self.meta.variables
        self.text = self.meta.get_text()
        self.create_template()

    def create_template(self):
        raise NotImplementedError

    def substitute(self, values):
        raise NotImplementedError


class StringTemplateSnippet(BaseSnippet):

    def create_template(self):
        from string import Template
        self.template = Template(self.text)

    def substitute(self, values):
        return self.template.substitute(values)


class JinjaSnippet(BaseSnippet):

    def create_template(self):
        from jinja import from_string
        self.template = from_string(self.text)

    def substitute(self, values):
        return self.template.render(values)

class CommunitySnippetMeta(object):

    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.meta = data_dict['meta']

    def save_as(self, filename):
        pass

    def generate_filename(self):
        pass


class SnippetMeta(object):
    
    def __init__(self, filename):
        self.filename = filename
        self.template_filename = self.filename.rsplit('.', 1)[0] + '.tmpl'
        self.read_metadata()
        self._text = None

    def get_configobj(self):
        return ConfigObj(self.filename)

    def read_metadata(self):
        config = self.get_configobj()
        self.name = config['meta']['name']
        self.title = config['meta']['title']
        self.shortcut = config['meta']['shortcut']
        self.variables = []
        for sect in config['variables']:
            self.variables.append(SnippetVariable(sect, config['variables'][sect]))

    def create_snippet(self):
        config = self.get_configobj()
        return StringTemplateSnippet(self)

    def get_text(self):
        if self._text is None:
            f = open(self.template_filename, 'r')
            self._text = f.read()
            f.close()
        return self._text
        

class SnippetActions(ActionsConfig):
    
    def create_actions(self):
        self.create_action(
            'insert_snippet',
            TYPE_NORMAL,
            _('Insert snippet from word'),
            _('Insert a snippet with the current word'),
            gtk.STOCK_ADD,
            self.on_insert_snippet,
            '<Shift><Control>g',
        )

        self.create_action(
            'show_snippets',
            TYPE_TOGGLE,
            _('Snippets manager'),
            _('Show the snippets'),
            gtk.STOCK_EXECUTE,
            self.on_show_snippets,
            ''
        )

    def on_show_snippets(self, action):
        if action.get_active():
            self.svc.show_snippets()
        else:
            self.svc.hide_snippets()

    def on_insert_snippet(self, action):
        self.svc.boss.editor.cmd('call_with_current_word',
                                callback=self.svc.popup_snippet)


# Service class
class Snippets(Service):
    """Describe your Service Here""" 
    actions_config = SnippetActions

    def start(self):
        self._view = SnippetsManagerView(self)
        self.snippets = {}
        self.create_snippet_directories()
        self.get_snippet_list()

    def add_snippet_meta(self, snippet_meta):
        self.snippets[snippet_meta.shortcut] = snippet_meta

    def create_snippet_directories(self):
        self._snippet_dir = os.path.join(self.boss.get_pida_home(), 'snippets')
        if not os.path.exists(self._snippet_dir):
            os.mkdir(self._snippet_dir)

    def get_snippet_list(self):
        self._view.clear_installed()
        task = GeneratorTask(self._list_snippets, self._list_snippets_got)
        task.start()
        
    def _list_snippets(self):
        for name in os.listdir(self._snippet_dir):
            if name.endswith('.meta'):
                yield SnippetMeta(os.path.join(self._snippet_dir, name))

    def _list_snippets_got(self, snippet_meta):
        self.add_snippet_meta(snippet_meta)
        self._view.add_installed(snippet_meta)

    def get_available_snippets(self):
        self.boss.cmd('notify', 'notify', title='Snippets', data='Fetching available snippets')
        self._view.clear_available()
        task = GeneratorTask(
            self._available_snippets,
            self._available_snippets_got,
            self._available_snippets_completed,    
        )
        task.start()

    def _available_snippets(self):
        for snippet_id, snippet_data in server_proxy.snippet.get([]).items():
            yield CommunitySnippetMeta(snippet_data)

    def _available_snippets_got(self, snippet_meta):
        print snippet_meta

    def _available_snippets_completed(self):
        self.boss.cmd('notify', 'notify', title='Snippets', data='Fetching available snippets')
        print 'completed'
        
        
        
    def popup_snippet(self, word):
        try:
            snippet = self.snippets[word].create_snippet()
        except KeyError:
            self.error_dlg('Snippet does not exist')
            return
        popup = SnippetWindow(snippet, self.snippet_completed)
        popup.set_transient_for(self.window)
        popup.show_all()

    def snippet_completed(self, success, text):
        if success:
            self.insert_snippet(text)

    def insert_snippet(self, text):
        self.boss.editor.cmd('delete_current_word')
        self.boss.editor.cmd('insert_text', text=text)

    def show_snippets(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        #self.update_installed_snippets()

    def hide_snippets(self):
        self.boss.cmd('window', 'remove_view', view=self._view)


# Required Service attribute for service loading
Service = Snippets


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
