
import gtk

ORIENTATION_SIDEBAR_LEFT = 0
ORIENTATION_SIDEBAR_RIGHT = 1

BOOK_TERMINAL = 'Terminal'
BOOK_EDITOR = 'Editor'
BOOK_BUFFER = 'Buffer'
BOOK_PLUGIN = 'Plugin'

class BaseBookConfig(object):
    
    def __init__(self, orientation):
        self._orientation = orientation

    def get_tabs_visible(self):
        return True

    def get_tab_position(self):
        return gtk.POS_TOP

    def get_notebook_name(self):
        raise NotImplementedError('Must at least define a notebook name')

    def get_name(self):
        raise NotImplementedError('Must at leaste define a Name')


class TerminalBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'br_book'
        else:
            return 'bl_book'

    def get_name(self):
        return 'Terminal'


class EditorBookConfig(BaseBookConfig):
    
    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'tr_book'
        else:
            return 'tl_book'

    def get_tabs_visible(self):
        return False

    def get_name(self):
        return 'Editor'


class BufferBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'tl_book'
        else:
            return 'tr_book'

    def get_tab_position(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return gtk.POS_RIGHT
        else:
            return gtk.POS_LEFT

    def get_name(self):
        return 'Buffer'

class PluginBookConfig(BaseBookConfig):

    def get_notebook_name(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return 'bl_book'
        else:
            return 'br_book'

    def get_tab_position(self):
        if self._orientation == ORIENTATION_SIDEBAR_LEFT:
            return gtk.POS_RIGHT
        else:
            return gtk.POS_LEFT
    
    def get_name(self):
        return 'Plugin'

class BookConfigurator(object):
    
    def __init__(self, orientation):
        self._orientation = orientation
        self._configs = {}
        self._books = {}
        for conf in [
            TerminalBookConfig,
            EditorBookConfig,
            PluginBookConfig,
            BufferBookConfig
        ]:
            self._configs[conf] = conf(self._orientation)
            self._books[conf] = None

    def _get_config(self, name):
        for conf in self._configs.values():
            if conf.get_notebook_name() == name:
                return conf
        raise KeyError('No Notebook attests to having that name')

    def configure_book(self, name, book):
        conf = self._get_config(name)
        self._books[conf.get_name()] = book
        book.set_show_tabs(conf.get_tabs_visible())
        book.set_tab_pos(conf.get_tab_position())
        book.remove_page(0)

    def get_book(self, name):
        return self._books[name]

    def get_names(self):
        return self._books.keys()


class BookManager(object):

    def __init__(self, configurator):
        self._conf = configurator
        self._views = dict.fromkeys(self._conf.get_names())

    def add_view(self, name, view):
        pass
        




