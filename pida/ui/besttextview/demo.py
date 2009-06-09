import gtk
from pida.services.language import DOCTYPES

__package__ = 'pida.ui.besttextview'
import pida.ui.besttextview

if __name__ == '__main__':
    try:
        from .mooview import MooTextView
    except ImportError:
        MooTextView = None

    try:
        from .sourceview import SourceTextView
    except ImportError:
        SourceTextView = None

    try:
        from .textview import SimpleTextView
    except ImportError:
        SimpleTextView = None

    allw = (x for x in (MooTextView, SourceTextView, SimpleTextView) if x)

    win = gtk.Window()
    box = gtk.VBox()
    win.add(box)

    txt = open(__file__, 'r').read(-1)
    
    for widget in allw:
        widg = widget()
        scr = gtk.ScrolledWindow()
        widg.get_buffer().set_text(txt)
        widg.set_doctype(DOCTYPES['Python'])
        widg.set_show_line_numbers(True)
        scr.add(widg)
        box.add(scr)

    win.show_all()
    win.connect('delete-event', gtk.main_quit)
    win.resize(550, 350)
    gtk.main()