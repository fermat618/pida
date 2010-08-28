
from functools import partial
from xml.sax.saxutils import escape

from pygtkhelpers.ui.objectlist import Column, Cell
from pygtkhelpers.ui.widgets import AttrSortCombo

from pida.ui.views import PidaView
from .buffer import _, locale

attributes = {
    'onerow': 'markup',
    'tworow': 'markup_tworow',
}

markup_extras = {
    'directory_color': 'blue',
    'project_color': 'darkviolet',
}

markup_attributes = [
    'project_name',
    'project_relative_path',
    'basename',
    'filename',
    'directory',
]
markup_strings = {
    'onerow_project': (
        u'<span color="{project_color}">'
        u'{project_name}</span><tt>:</tt>'
        u'<span color="{directory_color}">'
        u'{project_relative_path}/</span>'
        u'<b>{basename}</b>'
    ),
    'onerow_fullpath': (
        u'<span color="{directory_color}">'
        u'{directory}/</span>'
        u'<b>{basename}</b>'
    ),
    'tworow_project': (
        u'<b>{basename}</b>\n'
        u'<small>'
        u'<span foreground="{project_color}">'
        u'{project_name}</span><tt>:</tt>'
        u'<span foreground="{directory_color}">'
        u'{project_relative_path}/</span>'
        u'{basename}'
        u'</small>'
    ),
    'tworow_fullpath': (
        u'<b>{basename}</b>\n'
        u'<small>'
        u'<span foreground="{directory_color}">'
        u'{directory}/</span>'
        u'{basename}'
        u'</small>'
    ),

}


def markup_dict(doc, **kw):
    for attr in markup_attributes:
        var = getattr(doc, attr)
        kw[attr] = escape(var) if var else ''
    return kw


def render(doc, markup):
    if doc.project:
        markup = markup_strings['%s_project' % markup]
    else:
        markup = markup_strings['%s_fullpath' % markup]
    data = markup_dict(doc)
    data.update(markup_extras)
    return markup.format(**data)


class BufferListView(PidaView):

    key = 'buffer.list'
    builder_file = 'buffer_list'
    locale = locale
    icon_name = 'package_office'

    label_text = _('Buffers')

    def create_ui(self ):
        self.buffers_ol.set_columns([
            Column('markup', cells=[
                Cell(None, use_markup=True,
                     format_func=partial(render, markup='onerow'))
            ]),
            Column('markup_tworow', visible=False, cells=[
                Cell(None, use_markup=True,
                     format_func=partial(render, markup='tworow'))
            ]),
            Column("basename", visible=False, searchable=True),
        ])

        self.buffers_ol.set_headers_visible(False)
        self._sort_combo = AttrSortCombo(self.buffers_ol,
            [
                ('creation_time', _('Time Opened')),
                ('filename', _('File path')),
                ('basename', _('File name')),
                ('mimetype', _('Mime Type')),
                ('doctype', _('Document Type')),
                ('length', _('File Length')),
                ('modified_time', _('Last Modified')),
                ('usage', _('View Counter')),
                ('last_opend', _('Last Opened')),
                #('Project', _('Project_name'))
            ],
            'creation_time' 
        )
        self._sort_combo.show()
        self.toplevel.pack_start(self._sort_combo, expand=False)

    def add_document(self, document):
        self.buffers_ol.append(document)

    def remove_document(self, document):
        self.buffers_ol.remove(document)

    def set_document(self, document):
        if self.buffers_ol.selected_item is not document:
            self.buffers_ol.selected_item = document

    def view_document(self, document):
        self.svc.view_document(document)
        self.svc.boss.editor.cmd('grab_focus')

    def on_buffers_ol__item_double_clicked(self, ol, item, ev=None):
        self.view_document(item)

    def on_buffers_ol__item_activated(self, ol, item):
        self.view_document(item)

    def on_buffers_ol__item_right_clicked(self, ol, item, event=None):
        menu = self.svc.boss.cmd('contexts', 'get_menu', context='file-menu',
                                 document=item, file_name=item.filename)

        # Add some stuff to the menu
        close = self.svc.get_action('close_selected').create_menu_item()
        menu.insert(close, 2)

        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

        # Must leave the menu in the same state we found it!
        def on_deactivate(menu):
            #menu.remove(sep)
            menu.remove(close)

        menu.connect('deactivate', on_deactivate)

    def get_current_buffer_index(self):
        return self.buffers_ol.selected_item

    def select_buffer_by_index(self, index):
        self.buffers_ol.select(self.buffers_ol[index])
        self.view_document(self.buffers_ol[index])

    # note current is the current buffer, not the current selected buffer
    def next_buffer(self):
        next = self.buffers_ol.item_after(self.svc.get_current())
        if next is None:
            next = self.buffers_ol[0]
        self.svc.open_file(document=next)

    def prev_buffer(self):
        prev = self.buffers_ol.item_before(self.svc.get_current())
        if prev is None:
            prev = self.buffers_ol[-1]
        self.svc.open_file(document=prev)

    def sort(self):
        self.buffers_ol.get_model().sort_column_changed()

    def set_display_attr(self, newattr):
        for attr in attributes.values():
            for col in self.buffers_ol._viewcols_for_attr(attr):
                col.props.visible = attr==newattr

