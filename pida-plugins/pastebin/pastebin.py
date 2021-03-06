# -*- coding: utf-8 -*- 

import gtk, gobject

from pygtkhelpers.ui.objectlist import ObjectList, Column
from pygtkhelpers.proxy import proxy_for
# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import (TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, 
                               TYPE_REMEMBER_TOGGLE)

from pida.ui.views import PidaView

from pida.utils.web import fetch_url

# locale
from pida.core.locale import Locale
locale = Locale('pastebin')
_ = locale.gettext


class Bin(object):
    """ A Pastebin """

    PASTE_URL = None

    def __init__(self, svc):
        self.svc = svc

    def create_data_dict(self, title, name, content, syntax):
        """
        Has to return a dict containing the POST data to send to the pastebin.
        Override this in individual pastebins.
        """

    @classmethod
    def get_syntax_items(cls):
        """
        Override to return a list of syntax item tuples (label, value)
        """

    def post(self, *args):
        self.args = args
        fetch_url(self.PASTE_URL, self.on_posted, self.create_data_dict(*args))

    def on_posted(self, url, content):
        self.svc._view.stop_pulse()
        if url:
            # pasting was successfully
            self.svc.new_paste_complete(url, *self.args)
        else:
            # an error occured when pasting
            self.svc.new_paste_failed(content)


class LodgeIt(Bin):

    PASTE_URL = 'http://paste.pocoo.org'

    def create_data_dict(self, title, name, content, syntax):
        return {
            'code':     content,
            'language': syntax
        }

    @classmethod
    def get_syntax_items(cls):
        return [
            ('Text', 'text'),
            ('Python', 'python'),
            ('Python Console Sessions', 'pycon'),
            ('Python Tracebacks', 'pycon'),
            ('PHP', 'html+php'),
            ('Django / Jinja Templates', 'html+django'),
            ('Mako Templates', 'html+mako'),
            ('Myghty Templates', 'html+myghty'),
            ('Apache Config (.htaccess)', 'apache'),
            ('Bash', 'bash'),
            ('Batch (.bat)', 'bat'),
            ('C', 'c'),
            ('C++', 'cpp'),
            ('C#', 'csharp'),
            ('CSS', 'css'),
            ('D', 'd'),
            ('MiniD', 'minid'),
            ('Smarty', 'smarty'),
            ('HTML', 'html'),
            ('Genshi Templates', 'html+genshi'),
            ('JavaScript', 'js'),
            ('Java', 'java'),
            ('JSP', 'jsp'),
            ('Lua', 'lua'),
            ('Haskell', 'haskell'),
            ('Scheme', 'scheme'),
            ('Ruby', 'ruby'),
            ('eRuby / rhtml', 'rhtml'),
            ('TeX / LaTeX', 'tex'),
            ('XML', 'xml'),
            ('reStructuredText', 'rst'),
            ('IRC Logs', 'irc'),
            ('Unified DIff', 'diff'),
            ('Vim Scripts', 'vim')
        ]


class Dpaste(Bin):

    PASTE_URL = 'http://dpaste.com/'

    def create_data_dict(self, title, name, content, syntax):
        return dict(
            poster = name,
            title = title,
            content = content,
            language = syntax,
        )

    @classmethod
    def get_syntax_items(cls):
        return [
            ('Python', 'Python'),
            ('Python Interactive / Traceback', 'PythonConsole'),
            ('SQL', 'Sql'),
            ('HTML / Django Template', 'DjangoTemplate'),
            ('JavaScript', 'JScript'),
            ('CSS', 'Css'),
            ('XML', 'Xml'),
            ('Diff', 'Diff'),
            ('Ruby', 'Ruby'),
            ('Ruby HTML (ERB)', 'Rhtml'),
            ('Haskell', 'Haskell'),
            ('Apache Configuration', 'Apache'),
            ('Bash Script', 'Bash'),
            ('Plain Text', ''),
        ]


class Rafb(Bin):

    PASTE_URL = 'http://www.rafb.net/paste/paste.php'

    def create_data_dict(self, title, name, content, syntax):
        return dict(
            text=content,
            nick=name,
            desc=title,
            lang=syntax,
            cvt_tabs=4,
            submit=_('Paste')
        )

    @classmethod
    def get_syntax_items(cls):
        return [
            ('C89', 'C89'),
            ('C', 'C'),
            ('C++', 'C++'), 
            ('C#', 'C#'),
            ('Java', 'Java'),
            ('Pascal', 'Pascal'),
            ('Perl', 'Perl'),
            ('PHP', 'PHP'),
            ('PL/I', 'PL/I'),
            ('Python', 'Python'),
            ('Ruby', 'Ruby'),
            ('SQL', 'SQL'),
            ('VB', 'VB'),
            ('Plain Text', 'Plain Text')
        ]

class Twisted(Bin):

    PASTE_URL = 'http://deadbeefbabe.org/paste/freeform_post!!addPasting'

    def create_data_dict(self, title, name, content, syntax):
        return dict(
            author=name,
            text=content,
            addPasting='addPasting',
            _charset_='',
        )

    @classmethod
    def get_syntax_items(cls):
        return [('Python', '')]


class HPaste(Bin):
    PASTE_URL="http://hpaste.org/fastcgi/hpaste.fcgi/save"
    
    def create_data_dict(self, title, name, content, syntax):
        return dict(
            content=content,
            author=name,
            title=title,
            save='save',      
            language=syntax,
            channel='none',
        )
    
    @classmethod
    def get_syntax_items(cls):
        return [
            ("apacheconf","ApacheConf"),
            ("BBCode", "bbcode"),
            ("Bash", "bash"),
            ("C", "c"),
            ("C#", "csharp"),
            ("C++", "cpp"),
            ("CSS", "css"),
            ("Clojure", "clojure"),
            ("Common Lisp", "common-lisp"),
            ("D", "d"),
            ("HTML", "html"),
            ("Haskell", "haskell"),
            ("INI", "ini"),
            ("Io", "io"),
            ("Java", "java"),
            ("JavaScript", "js"),
            ("Lighttpd configuration file", "lighty"),
            ("Lua", "lua"),
            ("Makefile", "make"),
            ("Objective-C", "objective-c"),
            ("PHP", "php"),
            ("Perl", "perl"),
            ("Python", "python"),
            ("Python 3", "python3"),
            ("Python 3.0 Traceback", "py3tb"),
            ("Python Traceback", "pytb"),
            ("Python console session", "pycon"),
            ("Raw token data","raw"),
            ("Ruby", "rb"),
            ("SQL", "sql"),
            ("Scala", "scala"),
            ("Text only", "text"),
            ("VimL", "vim"),
            ("XML", "xml"),
            ("YAML", "yaml"),
            ("reStructuredText", "rst"),
            ("sqlite3con", "sqlite3"),
        ]


pastebin_types = [
    ('DPaste', Dpaste),
    ('Rafb.net', Rafb),
    ('LodgeIt', LodgeIt),
    ('HPaste', HPaste),
    #('Twisted', Twisted), #Broken for some reason
]


class PastebinEditorView(PidaView):

    key = 'pastebin.editor'
    gladefile = 'paste_editor'
    locale = locale
    label_text = _('Paste Editor')
    icon_name = gtk.STOCK_PASTE

    def create_ui(self):
        self.paste_location.set_choices(self.svc.get_pastebin_types(), None)
        self.paste_proxy = proxy_for(self.paste_location)
        self.syntax_proxy = proxy_for(self.paste_syntax)

    def on_paste_proxy__changed(self, proxy, value):
        if value is not None:
            self.paste_syntax.set_choices(value.get_syntax_items(), None)

    def on_post_button__clicked(self, button):
        paste_type = self.paste_location.read()
        self.svc.commence_paste(paste_type, *self.read_values())

    def on_cancel_button__clicked(self, button):
        self.svc.cancel_paste()

    def read_values(self):
        return (self.paste_title.get_text(),
                self.paste_name.get_text(),
                self.paste_content.get_buffer().get_text(
                    self.paste_content.get_buffer().get_start_iter(),
                    self.paste_content.get_buffer().get_end_iter(),
                ),
                self.syntax_proxy.read(),
        )

    def can_be_closed(self):
        self.svc.cancel_paste()

class PasteHistoryView(PidaView):

    key = 'pastebin.history'

    label_text = _('Paste History')
    icon_name = gtk.STOCK_PASTE

    #glade_file_name = 'paste-history.glade'

    def create_ui(self):
        self.history_tree = ObjectList(
            [Column('markup', use_markup=True, expand=True)])
        self.history_tree.set_headers_visible(False)
        self.add_main_widget(self.history_tree)
        self.x11_clipboard = gtk.Clipboard(selection="PRIMARY")
        self.gnome_clipboard = gtk.Clipboard(selection="CLIPBOARD")
        self.history_tree.connect('item-right-clicked', self.on_paste_rclick)
        self.__pulse_bar = gtk.ProgressBar()
        self.add_main_widget(self.__pulse_bar, expand=False)
        # only show pulse bar if working
        self.__pulse_bar.hide()
        self.__pulse_bar.set_size_request(-1, 12)
        self.__pulse_bar.set_pulse_step(0.01)
        self.history_tree.show_all()

    @property
    def tree_selected(self):
        return self.history_tree.selected_item

    def set(self, pastes):
        '''Sets the paste list to the tree view.
           First reset it, then rebuild it.
        '''
        self.history_tree.clear()
        self.history_tree.expand(pastes)
        self.tree_selected = None

    def add_paste(self, item):
        self.history_tree.append(item)

    def copy_current_paste(self):
        '''Callback function bound to the toolbar button view that copies the
        selected paste'''
        if self.tree_selected != None:
            self.x11_clipboard.set_text(self.tree_selected.get_url())
            self.gnome_clipboard.set_text(self.tree_selected.get_url())

    def view_current_paste(self):
        '''Callback function bound to the toolbar button view that shows the
        selected paste'''
        if self.tree_selected != None:
            self.service.boss.call_command('pastemanager','view_paste',
                paste=self.tree_selected)
        else:
            print _("ERROR: No paste selected")

    def remove_current_paste(self):
        '''Callback function bound to the toolbar button delete that removes the
        selected paste'''
        if self.tree_selected != None:
            self.service.boss.call_command('pastemanager','delete_paste',
                paste=self.tree_selected)
        else:
            print _("ERROR: No paste selected")


    def cb_paste_db_clicked(self, ol, item):
        """
        Callback function called when an item is double clicked, and copy it
        to the gnome/gtk clipboard
        """
        if item is not None:
            self.svc.boss.cmd('browseweb', 'browse', url=item.url)
            # self.__gnome_clipboard.set_text(self.__tree_selected.get_url())
            # aa: view the paste

    def cb_paste_m_clicked(self,paste,tree_item):
        '''Callback function called when an item is middle clicked, and copy it
        to the mouse buffer clipboard'''
        if self.__tree_selected != None:
            self.__x11_clipboard.set_text(self.__tree_selected.get_url())

    def cb_paste_r_clicked(self, paste, tree_item, event):
        menu = gtk.Menu()
        sensitives = (tree_item is not None)
        for action in ['pastemanager+new_paste',
                        None,
                       'pastemanager+remove_paste',
                       'pastemanager+view_paste',
                        None,
                        'pastemanager+copy_url_to_clipboard']:
            if action is None:
                menu.append(gtk.SeparatorMenuItem())
            else:
                act = self.service.action_group.get_action(action)
                if 'new_paste' not in action:
                    act.set_sensitive(sensitives)
                mi = gtk.ImageMenuItem()
                act.connect_proxy(mi)
                mi.show()
                menu.append(mi)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def on_paste_rclick(self, ol, item, event):
        self.svc.boss.cmd('contexts', 'popup_menu', context='url-menu',
                          url=item.url, event=event)

    def start_pulse(self):
        '''Starts the pulse'''
        self._pulsing = True
        self.__pulse_bar.show()
        gobject.timeout_add(100, self._pulse)

    def stop_pulse(self):
        self.__pulse_bar.hide()
        self._pulsing = False

    def _pulse(self):
        self.__pulse_bar.pulse()
        return self._pulsing

    def can_be_closed(self):
        self.svc.get_action('show_pastes').set_active(False)


class PastebinActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'new_paste',
            TYPE_NORMAL,
            _('Upload Text Snippet'),
            _('Upload a text snippet to a pastebin'),
            gtk.STOCK_PASTE,
            self.on_new_paste,
        )

        self.create_action(
            'show_pastes',
            TYPE_REMEMBER_TOGGLE,
            _('Paste History'),
            _('Show the paste history viewer'),
            gtk.STOCK_PASTE,
            self.on_show_pastes,
            '<Shift><Control>0',
        )

    def on_new_paste(self, action):
        self.svc.new_paste()

    def on_show_pastes(self, action):
        if action.get_active():
            self.svc.show_pastes()
        else:
            self.svc.hide_pastes()

class PasteItem(object):

    def __init__(self, url, *args):
        self.url = url
        self.title, self.name, self.content, self.syntax = args

    @property
    def markup(self):
        return ('<b>%s</b> (<span foreground="#0000c0">%s</span>)\n%s' %
                    (self.title, self.syntax, self.url))


# Service class
class Pastebin(Service):
    """Describe your Service Here""" 

    actions_config = PastebinActionsConfig

    def pre_start(self):
        self._editor = PastebinEditorView(self)
        self._view = PasteHistoryView(self)

    def new_paste(self):
        self.boss.cmd('window', 'add_view', paned='Plugin',
                      view=self._editor)
        self.get_action('new_paste').set_sensitive(False)

    def show_pastes(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_pastes(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def commence_paste(self, paste_type, *args):
        p = paste_type(self)
        p.post(*args)
        self.ensure_view_visible()
        self._view.start_pulse()
        self._close_paste_editor()

    def cancel_paste(self):
        self._close_paste_editor()

    def _close_paste_editor(self):
        self.boss.cmd('window', 'remove_view', view=self._editor)
        self.get_action('new_paste').set_sensitive(True)

    def new_paste_complete(self, url, *args):
        self._view.add_paste(PasteItem(url, *args))
        self.ensure_view_visible()

    def new_paste_failed(self, response):
        self.boss.cmd('notify', 'notify', title=response,
            data=_('An error occured when pasting.\n'
                   'Maybe you should try to use another pastebin?'))

        # show editor field
        self.new_paste()


    def ensure_view_visible(self):
        act = self.get_action('show_pastes')
        if not act.get_active():
            act.set_active(True)

    def get_pastebin_types(self):
        return pastebin_types

    def stop(self):
        if not self.get_action('new_paste').get_sensitive():
            self._close_paste_editor()
        if self.get_action('show_pastes').get_active():
            self.hide_pastes()

# Required Service attribute for service loading
Service = Pastebin



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
