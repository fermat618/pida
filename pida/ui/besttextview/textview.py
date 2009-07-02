import gtk
from .base import BaseTextView

class SimpleTextView(gtk.TextView, BaseTextView):
    """
    Simple gtk.TextView based Field without syntax highlighting
    """
