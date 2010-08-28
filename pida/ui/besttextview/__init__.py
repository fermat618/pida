
views = [
    'pida.ui.besttextview.mooview.MooTextView',
    'pida.ui.besttextview.sourceview.SourceTextView',
    'pida.ui.besttextview.textview.SimpleTextView',
]

def import_view(views):
    module, name = view.rsplit('.', 1)
    module = __import__(module, fromlist=['*'])
    return getattr(module, name)

for view in views:
    try:
        BestTextView = import_view(view)
    except ImportError:
        pass


__all__ = ['BestTextView']
