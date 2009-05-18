import gtk
from .base import BaseTextView
import gtksourceview

from pida.services.language import DOCTYPES

MAPPINGS = {}
LANG_MANAGER = gtksourceview.SourceLanguagesManager()

def build_mapping():
    global MAPPINGS, LANG_MANAGER
    for lang in LANG_MANAGER.get_available_languages():
        best = DOCTYPES.get_fuzzy(lang.get_name())
        if best:
            MAPPINGS[best.internal] = lang

build_mapping()

class SourceTextView(BaseTextView, gtksourceview.SourceView):
    """
    Simple gtk.TextView based Field without syntax highlighting
    """
    has_syntax_highlighting = True

    def __init__(self):
        buffer_ = gtksourceview.SourceBuffer()
        gtksourceview.SourceView.__init__(self, buffer_)

    def set_doctype(self, doctype):
        self._doctype = doctype
        buffer_ = self.get_buffer()
        buffer_.set_language(MAPPINGS.get(doctype.internal, None))
        buffer_.set_highlight(True)

    def set_show_line_numbers(self, value):
        self.props.show_line_numbers = value

    def get_show_line_numbers(self, value):
        return self.props.show_line_numbers