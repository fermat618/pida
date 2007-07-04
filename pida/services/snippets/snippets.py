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
from kiwi.ui.objectlist import Column


# locale
from pida.core.locale import Locale
locale = Locale('snippets')
_ = locale.gettext



import gtk, gobject

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


class SnippetWindow(gtk.Window):

    def __init__(self, snippet, response_callback):
        gtk.Window.__init__(self)
        self.response_callback = response_callback
        self.set_decorated(False)
        self.add_events(gtk.gdk.FOCUS_CHANGE_MASK)
        #self.connect('set-focus-child', self.on_focus_child)
        self.connect('focus-out-event', self.focus_out)
        self.connect('focus-in-event', self.focus_in)

        self._create_ui()
        self._vals = {}
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
        entry = gtk.Entry()
        entry.set_text(default)
        self._vals[name] = default
        hb.pack_start(entry, expand=False)
        entry.connect('changed', self.on_entry_changed, name)
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
        self.preview()

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
        print 'fo'

    def focus_in(self, window, event):
        print  'fi'

    def close(self):
        self.hide_all()
        self.destroy()

    def respond_success(self):
        self.response_callback(True, self.get_substituted_text())
        self.close()

    def response_failure(self):
        self.response_callback(False, None)
        self.close()

class MockSnippet(object):

    def __init__(self):
        self.title = 'HTML Tag'
        #from string import Template
        #self._t = Template('<$tag class="$class">\n</$tag>')
        from jinja import from_string
        self._t = from_string("""<{{ tag }}{% if class %} class="{{ class }}"{% endif %}>\n</{{ tag }}>""")

        #self._defaults = {'class': '', 'extra': ''}
        self._t = from_string(
'''
{#
This is a comment
#}
class {{ name }}({% if super %}{{ super }}{% else %}object{% endif %}):
{% if docstring %}    """{{ docstring }}"""\n{% endif %}
    def __init__(self):
'''
)

    def get_variables(self):
        #nodupes = []
        #[nodupes.append(''.join(i)) for i in
        #self._t.pattern.findall(self._t.template) if ''.join(i) not in nodupes]
        return ['name', 'super', 'docstring']

    def substitute(self, vals):
        #newvals = dict(vals)
        #for k in self._defaults:
        #    if k not in newvals:
        #        newvals[k] = self._defaults[k]
        return self._t.render(vals)

class MissingSnippetMetadata(Exception):
    """The template had missing metadata"""


class SnippetVariable(object):

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.label = config['label']
        self.default = config['default']
        self.required = config.as_bool('required')

TEST_STRING_TEMPLATE = """
[ meta ]
    name = py_class
    title = Python Class
[ variables ]
    [[ name ]]
        label = Name
        default = 
        required = False
    [[ super ]]
        label = Super CLass
        default = object
        required = False
    [[ docstring ]]
        label = Docstring
        default = Enter a docstring
        required = False
[ template ]
text = '''class $name($super):  
    "$docstring"
'''
""".splitlines()

from configobj import ConfigObj

TEST_CONF = ConfigObj(TEST_STRING_TEMPLATE)

class BaseSnippet(object):
    
    def __init__(self, config):
        self.config = config
        try:
            self.name = self.config['meta']['name']
            self.title = self.config['meta']['title']
        except KeyError:
            raise MissingSnippetMetadata
        self.text = config['template']['text']
        self.get_variables()

    def get_variables(self):
        self.variables = []
        for sect in self.config['variables']:
            self.variables.append(SnippetVariable(sect, self.config['variables'][sect]))
        print self.variables

    def substitute(self, values):
        raise NotImplementedError


class StringTemplateSnippet(BaseSnippet):

    def __init__(self, config):
        BaseSnippet.__init__(self, config)
        from string import Template
        self.template = Template(self.text)

    def substitute(self, values):
        return self.template.substitute(values)


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
        self.snippets = {'p':{'c': StringTemplateSnippet(TEST_CONF)}}

    def popup_snippet(self, word):
        snippet_type, snippet_name = word[0], word[1:]
        snippet = self.snippets[snippet_type][snippet_name]
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
