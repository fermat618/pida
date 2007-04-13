import gtk

from kiwi.ui.delegates import Delegate
from kiwi.ui.dialogs import save, open as opendlg, info, error, yesno#, get_input

from pida.ui.books import BookManager, BookConfigurator
from pida.ui.uimanager import PidaUIManager
#from pida.ui.docks import DockManager, DOCK_BUFFER, DOCK_PLUGIN, DOCK_EDITOR, \
#    DOCK_TERMINAL
from pida.ui.paneds import PidaPaned

from pida.core.environment import get_uidef_path


class MainDelegate(Delegate):

    def __init__(self, boss, *args, **kw):
        self._boss = boss
        self._window = gtk.Window()
        Delegate.__init__(self, toplevel=self._window, delete_handler=self._on_delete_event, *args, **kw)
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

    # Window API
    
    def resize(self, width, height):
        self._window.resize(width, height)



class PidaWindow(MainDelegate):

    """Main PIDA Window"""


    def create_all(self):
        #self._fix_books()
        #self._fix_docks()
        self._fix_paneds()
        self._create_ui()
        self.resize(800, 600)

    def start(self):
        self._start_ui()

    def _create_ui(self):
        self._uim = PidaUIManager()
        self.main_box = gtk.VBox()
        self.top_box = gtk.VBox()
        self.bottom_box = gtk.VBox()
        self.main_box.pack_start(self.top_box, expand=False)
        self.main_box.pack_start(self._paned)
        self.main_box.pack_start(self.bottom_box, expand=False)
        self._window.add(self.main_box)
        
    def _start_ui(self):
        self._menubar = self._uim.get_menubar()
        self._toolbar = self._uim.get_toolbar()
        self.top_box.pack_start(self._menubar, expand=False)
        self.top_box.pack_start(self._toolbar, expand=False)
        self.top_box.show_all()
        self.main_box.show_all()

    def _fix_paneds(self):
        self._paned = PidaPaned()

    def _fix_docks(self):
        self._dock_man = DockManager()
        self.left_paned.pack1(self._dock_man.get_dock(DOCK_BUFFER))
        self.left_paned.pack2(self._dock_man.get_dock(DOCK_PLUGIN))
        self.right_paned.pack1(self._dock_man.get_dock(DOCK_EDITOR))
        self.right_paned.pack2(self._dock_man.get_dock(DOCK_TERMINAL))
        self.right_paned.show_all()
        self.left_paned.show_all()

    def _fix_books(self):
        self._book_config = BookConfigurator(0)
        for n in ['tl', 'tr', 'bl', 'br']:
            book_name = '%s_book' % n
            book = getattr(self, book_name)
            self._book_config.configure_book(book_name, book)
        self._book_man = BookManager(self._book_config)

    # Action group API
    def add_action_group(self, actiongroup):
        self._uim.add_action_group(actiongroup)

    def add_uidef(self, filename):
        try:
            uifile = get_uidef_path(filename)
            self._uim.add_ui_from_file(uifile)
        except Exception, e:
            print 'unable to get %s resource' % filename

    # View API
    def add_view(self, bookname, view):
        self._paned.add_view(bookname, view)

    def remove_view(self, view):
        self._book_man.remove_view(view)

    def move_view(self, bookname, view):
        self._book_man.move_view(bookname, view)


