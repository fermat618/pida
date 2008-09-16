# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

"""
    pida.services.languages
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies support for languages


    :license: GPL2 or later
"""

import gtk
import pida.plugins

from kiwi.ui.objectlist import Column
from kiwi.ui.objectlist import ObjectList

#from pida.core.service import Service
#from pida.core.events import EventsConfig
#from pida.core.options import OptionsConfig
#from pida.core.actions import ActionsConfig, TYPE_TOGGLE
#from pida.utils.gthreads import GeneratorTask, AsyncTask, gcall
from pida.core.servicemanager import ServiceLoader

from pida.core.environment import plugins_dir


# core
from pida.core.service import Service
#from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.objectlist import AttrSortCombo


# locale
from pida.core.locale import Locale
locale = Locale('plugins')
_ = locale.gettext

def get_value(tab, key):
    return tab.get(key, None)



class ValidatorView(PidaView):
    
    icon_name = 'python-icon'
    label_text = _('Language Errors')

    def create_ui(self):
        self.errors_ol = ObjectList(
            Column('markup', use_markup=True)
        )
        self.errors_ol.set_headers_visible(False)
        self.errors_ol.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_main_widget(self.errors_ol)
        self.errors_ol.connect('double-click', self._on_errors_double_clicked)
        self.errors_ol.show_all()
        self.sort_combo = AttrSortCombo(
            self.errors_ol,
            [
                ('lineno', _('Line Number')),
                ('message_string', _('Message')),
                ('name', _('Type')),
            ],
            'lineno',
        )
        self.sort_combo.show()
        self.add_main_widget(self.sort_combo, expand=False)

    def clear_items(self):
        self.errors_ol.clear()

    def set_items(self, items):
        self.clear_items()
        for item in items:
            self.errors_ol.append(self.decorate_pyflake_message(item))

    def decorate_pyflake_message(self, msg):
        args = [('<b>%s</b>' % arg) for arg in msg.message_args]
        msg.message_string = msg.message % tuple(args)
        msg.name = msg.__class__.__name__
        msg.markup = ('<tt>%s </tt><i>%s</i>\n%s' % 
                      (msg.lineno, msg.name, msg.message_string))
        return msg

    def _on_errors_double_clicked(self, ol, item):
        self.svc.boss.editor.cmd('goto_line', line=item.lineno)

    def can_be_closed(self):
        return True
        # FIXME
        #self.svc.get_action('show_python_errors').set_active(False)


class BrowserView(PidaGladeView):

    gladefile = 'outline-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Outliner')

    def create_ui(self):
        self.source_tree.set_columns(
            [
                #Column('linenumber'),
                #Column('ctype_markup', use_markup=True),
                #Column('nodename_markup', use_markup=True),
                Column('icon_name', use_stock=True),
                Column('rendered', use_markup=True, expand=True),
                Column('type_markup', use_markup=True),
                Column('sort_hack', visible=False),
                Column('line_sort_hack', visible=False),
            ]
        )
        self.source_tree.set_headers_visible(False)
        self.sort_box = AttrSortCombo(
            self.source_tree,
            [
                ('sort_hack', _('Alphabetical by type')),
                ('line_sort_hack', _('Line Number')),
                ('name', _('Name')),
            ],
            'sort_hack'
        )
        self.sort_box.show()
        self.main_vbox.pack_start(self.sort_box, expand=False)

    def clear_items(self):
        self.source_tree.clear()

    def add_node(self, node, parent):
        self.source_tree.append(parent, node)

    def can_be_closed(self):
        self.svc.get_action('show_outliner').set_active(False)

    def on_source_tree__double_click(self, tv, item):
        if item.linenumber is None:
            return
        if item.filename is not None:
            self.svc.boss.cmd('buffer', 'open_file', file_name=item.filename)
        self.svc.boss.editor.cmd('goto_line', line=item.linenumber)
        self.svc.boss.editor.cmd('grab_focus')

    def on_show_super__toggled(self, but):
        self.browser.refresh_view()

    def on_show_builtins__toggled(self, but):
        self.browser.refresh_view()

    def on_show_imports__toggled(self, but):
        self.browser.refresh_view()




class LanguageActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'show_validator',
            TYPE_TOGGLE,
            _('Validator'),
            _('Show the language validator'),
            'error',
            self.on_show_validator,
        )

        self.create_action(
            'show_browser',
            TYPE_TOGGLE,
            _('Outliner'),
            _('Show the language browser'),
            'info',
            self.on_show_browser,
        )

    def on_show_validator(self, action):
        if action.get_active():
            self.svc.show_validator()
        else:
            self.svc.hide_validator()

    def on_show_browser(self, action):
        if action.get_active():
            self.svc.show_browser()
        else:
            self.svc.hide_browser()

"""
class LanguageCommandsConfig(CommandsConfig):

    # Are either of these commands necessary?

    def present_validator_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_validator())

    def present_browser_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_browser())
"""

class LanguageOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'autoload',
            _('Autoload language support'),
            bool,
            True,
            _('Automaticly load language support on opening files'))


class LanguageFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        #self.subscribe_foreign('buffer', 'document-changed', self.on_document_changed)
        #self.subscribe_foreign('buffer', 'document-saved', self.on_document_changed)
        pass

#    def subscribe_all_foreign(self):
#        self.subscribe_foreign('buffer', 'document-changed',
#            self.buffer_changed)

    def on_document_changed(self, document):
        print "buffer changed", document
        self.svc.on_buffer_changed(document)


#class LanguageEvents(EventsConfig):
#
#    def create(self):
#        self.publish('plugin_started', 'plugin_stopped')


class Language(Service):
    """ Language manager service """

    actions_config = LanguageActionsConfig
    options_config = LanguageOptionsConfig
    #events_config = LanguageEvents
    features_config = LanguageFeatures

    def pre_start(self):
        self._check = False
        self._check_notify = False
        self._check_event = False
        self._loader = ServiceLoader(pida.plugins, test_file='language.pida')
        self._view_browser = BrowserView(self)
        self._view_validator = ValidatorView(self)
        self.task = None

    def start(self):
        self.autoload = self.opt('autoload')
        #self.update_installed_plugins(start=True)

    def show_validator(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_validator)

    def hide_validator(self):
        self.boss.cmd('window', 'remove_view', view=self._view_validator)

    def show_browser(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_browser)

    def hide_browser(self):
        self.boss.cmd('window', 'remove_view', view=self._view_browser)
    
    def on_buffer_changed(self, document):
        print document
        
    def start_language(self, name):
        pass
    
    def stop_language(self, name):
        pass

    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)
    


Service = Language

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
