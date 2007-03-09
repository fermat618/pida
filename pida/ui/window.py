import gtk

from kiwi.ui.delegates import GladeDelegate
from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input
from kiwi.environ import Library

from pida.ui.books import BookManager, BookConfigurator

library = Library('pida', root='../..')
library.add_global_resources(glade='glade')


class MainGladeDelegate(GladeDelegate):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        GladeDelegate.__init__(self, delete_handler=self._on_delete_event, *args, **kw)
        self.create_all()
        self.show()

    def _on_delete_event(self, window, event):
        if self.yesno_dlg('Are you sure you want to exit?'):
            self.hide_and_quit()
        else:
            return True

    def create_all(self):
        pass

    # Dialogs
    def save_dlg(self, *args, **kw):
        return save(parent = self.get_toplevel(), *args, **kw)

    def open_dlg(self, *args, **kw):
        return opendlg(parent = self.get_toplevel(), *args, **kw)

    def info_dlg(self, *args, **kw):
        return info(parent = self.get_toplevel(), *args, **kw)

    def error_dlg(self, *args, **kw):
        return error(parent = self.get_toplevel(), *args, **kw)

    def yesno_dlg(self, *args, **kw):
        return yesno(parent = self.get_toplevel(), *args, **kw) == gtk.RESPONSE_YES

    def error_list_dlg(self, msg, errs):
        return self.error_dlg('%s\n\n* %s' % (msg, '\n\n* '.join(errs)))

    def input_dlg(self, *args, **kw):
        return get_input(parent=self.get_toplevel(), *args, **kw)


class PidaWindow(MainGladeDelegate):

    """Main PIDA Window"""

    gladefile = 'main_window'

    def create_all(self):
        self._fix_books()

    def _fix_books(self):
        self._book_config = BookConfigurator(0)
        for n in ['tl', 'tr', 'bl', 'br']:
            book_name = '%s_book' % n
            book = getattr(self, book_name)
            self._book_config.configure_book(book_name, book)
        self._book_man = BookManager(self._book_config)

    # View API
    def add_view(self, bookname, view):
        self._book_man.add_view(bookname, view)

    def remove_view(self, view):
        self._book_man.remove_view(view)

    def move_view(self, bookname, view):
        self._book_man.move_view(bookname, view)


