try:
    from .mooview import MooTextView as BestTextView
except ImportError:
    try:
        from .sourceview import SourceTextView as BestTextView
    except ImportError:
        from .textview import SimpleTextView as BestTextView

__all__ = ['BestTextView']