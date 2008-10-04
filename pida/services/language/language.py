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


from pida.core.environment import plugins_dir

from pida.core.doctype import TypeManager
from pida.core.languages import LanguageInfo
from pida.utils.pdbus import EXPORT

from pida.utils.gthreads import GeneratorTask


# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_TOGGLE, TYPE_MENUTOOL, TYPE_NORMAL
from pida.core.options import OptionsConfig
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.pdbus import DbusConfig

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

    key = 'language.validator'

    icon_name = 'python-icon'
    label_text = _('Language Errors')

    def set_validator(self, validator):
        self.clear_nodes()
        if validator:
            task = GeneratorTask(validator.get_validations, self.add_node)
            task.start()

    def add_node(self, node):
        self.errors_ol.append(self.decorate_pyflake_message(node))

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

    def clear_nodes(self):
        self.errors_ol.clear()

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

    key = 'language.browser'


    gladefile = 'outline-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('Outliner')

    def create_ui(self):
        self.source_tree.set_columns(
            [
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

    def set_outliner(self, outliner):
        self.clear_items()
        self.options = self.read_options()
        if outliner:
            task = GeneratorTask(outliner.get_outline, self.add_node)
            task.start()

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

    def read_options(self):
        return {
            '(m)': self.show_super.get_active(),
            '(b)': self.show_builtins.get_active(),
            'imp': self.show_imports.get_active(),
        }


class LanguageActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'language_type',
            TYPE_MENUTOOL,
            _('_Type'),
            _('Select Document Type'),
            'package_utilities',
            self.on_type_change,
        )

        self.create_action(
            'language_type_menu',
            TYPE_NORMAL,
            _('_Type'),
            _('Select document type'),
            gtk.STOCK_EXECUTE,
            self.on_type_menu,
        )

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

        self.create_action(
            'goto_definition',
            TYPE_NORMAL,
            _('Goto Definition'),
            _('Goto the definition of current word'),
            'goto',
            self.on_goto_definition,
            'F5'
        )

    def on_type_change(self, action):
        pass

    def on_type_menu(self, action):
        menuitem = action.get_proxies()[0]
        menuitem.remove_submenu()
        menuitem.set_submenu(self.svc.create_menu())

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
            
    def on_goto_definition(self, action):
        print "goto definition", action
        


class LanguageCommandsConfig(CommandsConfig):

    # Are either of these commands necessary?

    def get_current_filetype(self):
        return self.svc.current_type

    def present_validator_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_validator())

    def present_browser_view(self):
        return self.svc.boss.cmd('window', 'present_view',
                                 view=self.svc.get_browser())


class LanguageOptionsConfig(OptionsConfig):
    pass
    #def create_options(self):
    #    self.create_option(
    #        'autoload',
    #        _('Autoload language support'),
    #        bool,
    #        True,
    #        _('Automaticly load language support on opening files'))


class LanguageFeatures(FeaturesConfig):

    def subscribe_all_foreign(self):
        pass


class LanguageEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed', self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-saved', self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-typchanged', self.on_document_type)

    def create(self):
        self.publish('plugin_started', 'plugin_stopped')

    def on_document_changed(self, document):
        self.svc.on_buffer_changed(document)

    def on_document_type(self, document):
        self.svc.on_buffer_typechanged(document)


class LanguageDbusConfig(DbusConfig):

    @EXPORT(out_signature = 'as', in_signature = 'ssi')
    def get_completions(self, base, buffer, offset):
        doc = self.svc.boss.cmd('buffer', 'get_current')
        completer = self.svc.get_completer(doc)
        if completer is not None:
            return completer.get_completions(base, buffer, offset)
        else:
            return []

    @EXPORT(out_signature = 'a{s(as)}', in_signature = 's')
    def get_info(self, lang):
        """Returns language info"""
        lst = self.svc.features[(lang, 'infos')]
        if lst:
            l = lst[0]
            return l.to_dbus()
        return {}

def _get_best(lst, document):
    nlst = list(lst)
    nlst.sort(cmp=lambda x, y: -1*cmp(
         x.func.priorty_for_document(document),
         y.func.priorty_for_document(document))
      )
    return nlst[0]


class Language(Service):
    """ Language manager service """

    actions_config = LanguageActionsConfig
    options_config = LanguageOptionsConfig
    events_config = LanguageEvents
    features_config = LanguageFeatures
    commands_config = LanguageCommandsConfig
    dbus_config = LanguageDbusConfig

    def pre_start(self):
        self.doctypes = TypeManager()
        import deflang
        self.doctypes._parse_map(deflang.DEFMAPPING)
        self._view_outliner = BrowserView(self)
        self._view_validator = ValidatorView(self)
        self.current_type = None
        # add default language info
        self.features.subscribe((None, 'info'), LanguageInfo) 

    def show_validator(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_validator)

    def hide_validator(self):
        self.boss.cmd('window', 'remove_view', view=self._view_validator)

    def show_browser(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view_outliner)

    def hide_browser(self):
        self.boss.cmd('window', 'remove_view', view=self._view_outliner)

    def on_buffer_typechanged(self, document):
        for k in ("_lng_outliner", "_lng_validator", "_lng_completer",
                 "_lng_definer"):
            if hasattr(document, k):
                delattr(document, k)

        self.on_buffer_changed(document)

    def _get_feature(self, document, feature, name, do=None):
        handler = getattr(document, name, None)
        if not handler:
            type_ = document.doctype
            factories = ()
            if type_:
                factories = self.features[(type_.internal, feature)]
            if not factories:
                # get typ unspecific factories
                factories = self.features[(None, feature)]
            if factories:
                handler = _get_best(factories, document)(document)
                setattr(document, name, handler)
                return handler
        else:
            return handler


    def on_buffer_changed(self, document):
        doctypes = self.doctypes.types_by_filename(document.filename)
        if not doctypes:
            self.current_type = None
            return
        self.current_type = document.doctype

        self._view_outliner.set_outliner(
            self._get_feature(document, 'outliner', '_lng_outliner'))

        self._view_validator.set_validator(
            self._get_feature(document, 'validator', '_lng_validator'))

        self._get_feature(document, 'completer', '_lng_completer')
        self._get_feature(document, 'definer', '_lng_definer')

    def get_info(self, document):
        return self._get_feature(document, 'info', '_lng_info')

    def get_outliner(self, document):
        return self._get_feature(document, 'outliner', '_lng_outliner')

    def get_validator(self, document):
        return self._get_feature(document, 'validator', '_lng_validator')

    def get_completer(self, document):
        return self._get_feature(document, 'completer', '_lng_completer')
        
    def get_definer(self, document):
        return self._get_feature(document, 'definer', '_lng_definer')

    def ensure_view_visible(self):
        action = self.get_action('show_plugins')
        if not action.get_active():
            action.set_active(True)
        self.boss.cmd('window', 'present_view', view=self._view)

    def change_doctype(self, widget, target):
        doc = self.boss.cmd('buffer', 'get_current')
        doc.doctype = target
        self.boss.get_service('buffer').emit('document-typchanged', document=doc)

    def create_menu(self):
        sections = {}
        menu = gtk.Menu()
        a = gtk.Action('None',
                'None',
                'No specific document type',
                gtk.STOCK_NEW)
        menu.add(a.create_menu_item())
        menu.add(gtk.SeparatorMenuItem())

        for target in self.doctypes.itervalues():
            act = gtk.Action(target.internal,
                target.human or target.internal,
                target.tooltip,
                '')
            act.connect('activate', self.change_doctype, target)
            mi = act.create_menu_item()
            if not sections.has_key(target.section):
                sections[target.section] = gtk.Menu()
                #menu.add(sections[target.section])
                ms = gtk.MenuItem(target.section)
                ms.set_submenu(sections[target.section])
                menu.add(ms)
                
            sections[target.section].add(mi)
        menu.show_all()
        return menu

Service = Language

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
