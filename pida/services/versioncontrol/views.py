import time

from cgi import escape

import gtk
import pango

from pygtkhelpers.gthreads import gcall

from pida.ui.htmltextview import HtmlTextView
from pida.ui.besttextview import BestTextView
from pida.ui.views import PidaView

from .versioncontrol import _


class HtmlDiffViewer(PidaView):

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
        hb.show_all()

    def set_diff(self, diff):
        data = highlight(diff, DiffLexer(), HtmlFormatter(noclasses=True))
        self._html.display_html(data)

    def can_be_closed(self):
        return True


class TextDiffViewer(PidaView):

    icon_name = gtk.STOCK_COPY
    label_text = _('Differences')

    def create_ui(self):
        hb = gtk.HBox()
        self.add_main_widget(hb)
        sb = gtk.ScrolledWindow()
        sb.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sb.set_shadow_type(gtk.SHADOW_IN)
        sb.set_border_width(3)
        self._txt = BestTextView()
        from pida.services.language import DOCTYPES
        self._txt.set_doctype(DOCTYPES['Diff'])
        self._txt.set_show_line_numbers(True)
        self._txt.modify_font(pango.FontDescription('mono'))
        #self._html.set_left_margin(6)
        #self._html.set_right_margin(6)
        sb.add(self._txt)
        hb.pack_start(sb)
        hb.show_all()

    def set_diff(self, diff):
        #data = highlight(diff, DiffLexer(), HtmlFormatter(noclasses=True))
        #self._html.display_html(data)
        self._txt.get_buffer().set_text(diff)
        self._txt.set_editable(False)

    def can_be_closed(self):
        return True

if not BestTextView.has_syntax_highlighting:
    try:
        from pygments import highlight
        from pygments.lexers import DiffLexer
        from pygments.formatters import HtmlFormatter
    except ImportError:
        DiffLexer = HtmlFormatter = lambda *k, **kw: None  # they get args

        def highlight(diff, *k):  # dummy in case of missing pygments
            return '<pre>\n%s</pre>\n' % escape(diff)

    DiffViewer = HtmlDiffViewer
else:
    DiffViewer = TextDiffViewer


class VersionControlLog(PidaView):

    key = 'versioncontrol.log'

    builder_file = 'version_control_log'

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
        gcall(self._scroll_to_end)

    def _scroll_to_end(self):
        # scroll to the end of the buffer
        self.log_text.scroll_to_iter(self._buffer.get_end_iter(), 0)

    def can_be_closed(self):
        self.svc.get_action('show_vc_log').set_active(False)


class CommitViewer(PidaView):

    key = 'versioncontrol.commit'

    builder_file = 'commit_dialog'

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
