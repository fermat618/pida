# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk, gobject

class PopupWindow(gtk.Window):

    __gtype_name__ = 'PopupWindow'

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_decorated(False)
        self.add_events(gtk.gdk.FOCUS_CHANGE_MASK)
        #self.connect('set-focus-child', self.on_focus_child)
        self.connect('focus-out-event', self.focus_out)
        self.connect('focus-in-event', self.focus_in)

    def focus_out(self, window, event):
        print 'fo'

    def focus_in(self, window, event):
        print  'fi'
    #def do_set_focus_child(self, widget):
    #    print widget

gobject.type_register(PopupWindow)

class PopupEntryWindow(PopupWindow):

    def __init__(self):
        PopupWindow.__init__(self)
        self._create_ui()
        self._vals = {}

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
        sw.set_size_request(200, 200)
        return sw

    def _create_entries_box(self):
        self._entries = {}
        self._entries_order = []
        self._entries_vb = gtk.VBox(spacing=6)
        self._label_sizer = gtk.SizeGroup(gtk.ORIENTATION_HORIZONTAL)
        return self._entries_vb

    def add_entry(self, name, label_text):
        hb = gtk.HBox(spacing=6)
        label = gtk.Label()
        label.set_text(label_text)
        self._label_sizer.add_widget(label)
        hb.pack_start(label)
        entry = gtk.Entry()
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
        self._preview_text.get_buffer().set_text(self._snippet.substitute(self._vals))

    def on_entry_keypress(self, entry, event, name):
        print name, [event.keyval, event.state, event.string]
        if event.string == '\r':
            if event.state & gtk.gdk.CONTROL_MASK:
                print 'would exit'
            else:
                index = self._entries_order.index(entry)
                if index == len(self._entries_order) - 1:
                    print 'would exit'
                else:
                    self._entries_order[index + 1].grab_focus()
        elif event.string == '\x1b':
            print 'would exit'
            

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
        

class MulitpleVariableWindow(PopupEntryWindow):

    def __init__(self, snippet):
        PopupEntryWindow.__init__(self)
        self._snippet = snippet
        self.set_title_label(self._snippet.title)
        self._create_entries()

    def _create_entries(self):
        for variable in self._snippet.get_variables():
            self.add_entry(variable, variable)


if __name__ == '__main__':
    w1 = gtk.Window()
    w1.resize(400, 400)
    w1.add(gtk.TextView())
    w1.show_all()
    w = MulitpleVariableWindow(MockSnippet())
    w.set_transient_for(w1)
    w.show_all()
    gtk.main()

