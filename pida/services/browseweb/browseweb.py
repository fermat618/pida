# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
import webbrowser

try:
    import webkit
except ImportError:
    webkit = None


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.actions import ActionsConfig

from pida.ui.views import PidaView

# locale
from pida.core.locale import Locale
locale = Locale('browseweb')
_ = locale.gettext

def get_url_mark(url):
    try:
        url, mark = url.rsplit('#', 1)
    except:
        mark = None
    return url, mark


class SearchBar(gtk.HBox):

    def __init__(self, html, label='Find:'):
        gtk.HBox.__init__(self)
        self.html = html
        self.set_border_width(3)
        self.set_spacing(3)

        self.label = gtk.Label(label)
        self.label.show()
        self.pack_start(self.label, expand=False)

        self.text = gtk.Entry()
        self.text.connect('activate', self.on_text__activate)
        self.text.show()
        self.pack_start(self.text)

        self.find_button = gtk.ToolButton(gtk.STOCK_FIND)
        self.find_button.connect('clicked', self.on_find_button__clicked)
        self.find_button.set_tooltip_text(_('Find'))

        self.close_button = gtk.ToolButton(gtk.STOCK_CLOSE)
        self.close_button.set_tooltip_text(_('Close'))
        self.close_button.connect('clicked', self.on_close_button__clicked)

        self.pack_start(self.find_button, expand=False)
        self.find_button.show()

        if html.has_highlight:
            self.highlight_button = gtk.ToggleToolButton(gtk.STOCK_BOLD)
            self.highlight_button.set_tooltip_text(_('Highlight'))
            self.highlight_button.connect('toggled', 
                                          self.on_highlight_button__toggled)
            self.highlight_button.set_active(True)

            self.pack_start(self.highlight_button, expand=False)
            self.highlight_button.show()

        self.pack_start(self.close_button, expand=False)
        self.close_button.show()

        self.set_no_show_all(True)

    def on_text__activate(self, entry):
        self.perform_search()

    def perform_search(self):
        search = self.text.get_text()
        self.html.search_text(search, False, True, True)

    def start_search(self):
        self.show()
        self.text.grab_focus()

    def end_search(self):
        self.hide()

    def on_find_button__clicked(self, button):
        self.perform_search()

    def on_close_button__clicked(self, button):
        self.end_search()

    def on_highlight_button__toggled(self, button):
        self.html.set_highlight(button.get_active())

class WebkitHtmlWidget(gtk.VBox):

    def __init__(self, manager=None):
        self.url = ''
        self.manager = manager
        gtk.VBox.__init__(self)
        self.create_ui()

    def create_ui(self):
        self.html = webkit.WebView()
        self.html.connect('navigation-requested',
                          self.on_html__navigation_requested)

        self.html.connect('load-started',
                          self.on_html__load_started)
        self.html.connect('load-progress-changed',
                          self.on_html__load_progress_changed)
        self.html.connect('load-finished',
                          self.on_html__load_finished)

        self.html.connect('key-press-event', self.on_key_press)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.html)
        self.progress = gtk.ProgressBar()
        self.progress.set_no_show_all(True)

        self.searchbar = SearchBar(self)

        self.pack_start(self.sw)
        self.pack_start(self.searchbar, expand=False)
        self.pack_start(self.progress, expand=False)
        self.show_all()

    def search_text(self, search, sensetive=False, forward=True, wrap=True):
        self.html.search_text(search, sensetive, forward, wrap)
        if self.has_highlight:
            self.html.unmark_text_matches()
            self.html.mark_text_matches(search, sensetive, 0)
            self.html.set_highlight_text_matches(True)


    def load_url(self, url):
        self.url = url
        self.title = url
        self.html.open(url)

    def on_html__navigation_requested(self, html, frame, request):
        return 0

    def on_html__load_started(self, page, frame):
        self.progress.show()
        self.manager.stop_button.set_sensitive(True)


    def on_html__load_finished(self, page, frame):
        self.title = frame.get_title()
        self.progress.hide()
        self.finished(self.url)

    def on_html__load_progress_changed(self, page, progress):
        self.progress.set_fraction(progress / 100.0)
        self.progress.set_text('%s%%' % progress)

    def stop(self):
        self.html.stop_loading()

    def back(self):
        self.html.go_back()

    def finished(self, url):
        self.manager.stop_button.set_sensitive(False)
        self.manager.location.set_text(url)
        self.manager.back_button.set_sensitive(self.html.can_go_back())

    def on_key_press(self, html, event):
        if event.keyval in (47, 102):
            self.searchbar.start_search()

    @property
    def has_highlight(self):
        return hasattr(self.html, 'unmark_text_matches')

    def set_highlight(self, active):
        self.html.set_highlight_text_matches(active)



class BrowserView(PidaView):
    ICON_NAME = 'gtk-library' 
    SHORT_TITLE = _('Browser')

    HAS_TITLE = False

    def create_ui(self):
        self.__browser = WebkitHtmlWidget(self)
        bar = gtk.HBox()
        self.back_button = gtk.ToolButton(stock_id=gtk.STOCK_GO_BACK)
        self.stop_button = gtk.ToolButton(stock_id=gtk.STOCK_STOP)
        bar.pack_start(self.back_button, expand=False)
        bar.pack_start(self.stop_button, expand=False)

        self.find_button = gtk.ToolButton(stock_id=gtk.STOCK_FIND)
        self.find_button.connect('clicked', self.cb_toolbar_clicked, 'find')
        bar.pack_start(self.find_button, expand=False)

        self.back_button.connect('clicked', self.cb_toolbar_clicked, 'back')
        self.stop_button.connect('clicked', self.cb_toolbar_clicked, 'stop')
        self.add_main_widget(bar, expand=False)
        self.location = gtk.Entry()
        bar.pack_start(self.location)
        self.location.connect('activate', self.cb_url_entered)
        self.add_main_widget(self.__browser)
        self.get_toplevel().show_all()
        self._close_callback=None

    def connect_closed(self, callback):
        self._close_callback = callback

    def cb_url_entered(self, entry):
        url = self.location.get_text()
        self.fetch(url)

    def fetch(self, url):
        self.__browser.load_url(url)

    def cb_toolbar_clicked(self, button, name):
        if name == 'back':
            self.__browser.back()
        elif name == 'stop':
            self.__browser.stop()
        elif name == 'find':
            self.__browser.searchbar.start_search()

    def can_be_closed(self):
        if self._close_callback is not None:
            self._close_callback(self)
        else:
            self.svc.boss.cmd('window', 'remove_view', view=self)


class WebCommands(CommandsConfig):

    def browse(self, url):
        self.svc.browse(url)

    def get_web_browser(self):
        return BrowserView

class WebFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        from pida.services.openwith import OpenWithItem
        
        internal = OpenWithItem({'name': "Open in Browser",
                                 'command': self.open_web_file,
                                 'glob': '*'})
        external = OpenWithItem({'name': "Open in External Browser",
                                 'command': self.open_web_external_file,
                                 'glob': '*'})

        self.subscribe_foreign('contexts', 'url-menu',
            (self.svc, 'webbrowser-url-menu.xml'))

        self.subscribe_foreign('openwith', 'file-menu',
            internal)
        self.subscribe_foreign('openwith', 'file-menu',
            external)

    def open_web_file(self, file_name):
        self.svc.browse("file://%s" %file_name)

    def open_web_external_file(self, file_name):
        webbrowser.open("file://%s" %file_name)

class WebActions(ActionsConfig):
    
    def create_actions(self):
        self.create_action(
            'open_url_for_url',
            gtk.Action,
            _('Open URL'),
            _('Open a url in the builtin browser'),
            gtk.STOCK_OPEN,
            self.on_open_url_for_url,
        )

        self.create_action(
            'copy_clipboard_for_url',
            gtk.Action,
            _('Copy URL to clipboard'),
            _('Copy this URL to the clipboard'),
            gtk.STOCK_COPY,
            self.on_copy_url_for_url,
        )

        self.create_action(
            'open_url_external_for_url',
            gtk.Action,
            _('Open URL in external web browser'),
            _('Open the selected URL in an external web browser'),
            'internet',
            self.on_open_url_external_for_url,
        )

    def on_open_url_for_url(self, action):
        url = action.contexts_kw['url']
        self.svc.browse(url)

    def on_copy_url_for_url(self, action):
        url = action.contexts_kw['url']
        for clipboard_type in ['PRIMARY', 'CLIPBOARD']:
            gtk.Clipboard(selection=clipboard_type).set_text(url)

    def on_open_url_external_for_url(self, action):
        url = action.contexts_kw['url']
        webbrowser.open(url)

# Service class
class Webbrowser(Service):
    """Describe your Service Here""" 

    commands_config = WebCommands
    features_config = WebFeatures
    actions_config = WebActions

    def pre_start(self):
        self._views = []

    def browse(self, url):
        if webkit is None:
            webbrowser.open(url)
        else:
            view = BrowserView(self)
            view.fetch(url)
            self.boss.cmd('window', 'add_view', paned='Terminal', view=view)

# Required Service attribute for service loading
Service = Webbrowser



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
