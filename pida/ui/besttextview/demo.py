import gtk
from pida.services.language import DOCTYPES

__package__ = 'pida.ui.besttextview'
from pida.ui.besttextview import views, import_view

if __name__ == '__main__':

    allw = []
    for view in views:
        try:
            allw.append(import_view(view))
        except ImportError:
            pass

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
