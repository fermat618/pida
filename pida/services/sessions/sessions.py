# -*- coding: utf-8 -*- 
"""
    Sessions Service
    ~~~~~~~~~~~~~~~~

    currently this saves the open files to a gconf list

    .. todo::
        * window/sudebar/paned positions

    :license: GPL2 or later
    :copyright: 2005-2008 by The PIDA Project
"""

from __future__ import with_statement

import gtk
import simplejson

from kiwi.ui.delegates import GladeDelegate
from kiwi.ui.dialogs import yesno

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig, manager
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.environment import get_plugin_global_settings_path
from pida.ui.gtkforms import DialogOptions, create_gtk_dialog

# locale
from pida.core.locale import Locale
locale = Locale('sessions')
_ = locale.gettext

LEXPORT = EXPORT(suffix='session')

class SessionWindow(GladeDelegate):
    """
    Session load window
    """
    gladefile = 'sessions'

    class Entry(object):
        """Entry in the Session list"""
        name = None
        files = []

    def __init__(self, svc):
        """
        The WorkspaceWindow is displayed whenever the user should choose a 
        workspace to run.
        
        @fire_command: dbus command to send to an already running 
        @command: run command when one workspace is choosen
        @spawn_new: on the default handle. spawn a new process
        """
        #self.set_role('workspace') 
        #self.set_name('Pidaworkspace')
        self.svc = svc

        super(SessionWindow, self).__init__()

        #self.set_role('workspace') 
        self.toplevel.set_name('Pidasession')

        from kiwi.ui.objectlist import Column

        self.session_list.set_columns([
            Column('name', expand=True, sorted=True)
        ])

        self.update_sessions()

    def update_sessions(self):
        """Updates the session list to reflect service.data list"""
        self.session_list.clear()
        for key, val in self.svc.data.iteritems():
            entry = SessionWindow.Entry()
            entry.name = key
            entry.files = val
            self.session_list.append(entry)

    def on_session_list__row_activated(self, widget, obj):
        self.svc.load_buffers(obj.files, session=obj.name)
        self.hide()

    def on_button_ok__clicked(self, widget):
        cur = self.session_list.get_selected()
        if cur:
            self.svc.load_buffers(cur.files)
            self.hide()
    
    def on_button_cancel__clicked(self, widget):
        self.hide()

    def on_UseSession__activate(self, widget):
        self.on_session_list__row_activated(widget,
                                            self.session_list.get_selected())

    def on_DelSession__activate(self, *args, **kwargs):
        opt = self.session_list.get_selected()
        if yesno(_('Do you really want to delete session %s ?') %opt.name,
                 parent = self.toplevel) == gtk.RESPONSE_YES:
            self.session_list.remove(opt)
            del self.svc.data[opt.name]
            self.svc.save_data()

    def _create_popup(self, event, *actions):
        menu = gtk.Menu()
        for act in actions:
            if act is not None:
                mi = act.create_menu_item()
            else:
                mi = gtk.SeparatorMenuItem()
            menu.add(mi)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def on_session_list__right_click(self, oli, target, event):
        self._create_popup(event, self.UseSession, None, self.DelSession)

    def on_sessions__close(self, *args):
        self.hide()


class SessionsOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'close_files_on_load',
            _('Clear before load'),
            bool,
            True,
            _('Close all the currently open documents before loading a session.'),
        )

        self.create_option(
            'load_last_files',
            _('Load last opened files on startup'),
            bool,
            True,
            _('Load last opened files on startup'),
            workspace=True
        )

        self.create_option(
            'open_files',
            _('Open Files'),
            list,
            [],
            _('The list of open files'),
            safe=False,
            workspace=True
        )

    gladefile = 'sessions-properties'
    label_text = _('Sessions Properties')
    icon_name = 'package_utilities'


class SessionsActionsConfig(ActionsConfig):
    def create_actions(self):

        self.create_action(
            'save_session',
            TYPE_NORMAL,
            _('Save session'),
            _('Save session'),
            '',
            self.on_session_save,
            ''
        )
        self.create_action(
            'save_session_as',
            TYPE_NORMAL,
            _('Save session as'),
            _('Save session as'),
            '',
            self.on_session_save_as,
            ''
        )
        self.create_action(
            'load_session',
            TYPE_NORMAL,
            _('Load session'),
            _('Load session'),
            '',
            self.on_session_load,
            ''
        )

    def on_session_load(self, *args):
        self.svc.load_session()

    def on_session_save(self, *args):
        self.svc.save()

    def on_session_save_as(self, *args):
        self.svc.save_as()


class SessionsEventsConfig(EventsConfig):

    def subscribe_all_foreign(self):    
        self.subscribe_foreign('buffer', 'document-closed', self.svc.save_files)
        self.subscribe_foreign('buffer', 'document-changed',
                               self.svc.save_files)
        self.subscribe_foreign('editor', 'started', self.svc.load_files)
        self.subscribe_foreign('editor', 'document-exception', 
                               self.svc.on_document_exception)

class SessionsDbusConfig(DbusConfig):

    @LEXPORT(out_signature='s')
    def get_session_name(self):
        return self.svc._current

    @LEXPORT(out_signature='as')
    def list_session_names(self):
        self.svc.load_data()
        return [self.svc.data.iterkeys()]

    @LEXPORT(in_signature="s", out_signature='as')
    def list_session_files(self, name):
        return self.svc.data[name]

    @LEXPORT(in_signature='s')
    def load_session(self, name):
        files = self.svc.data[name]
        self.svc.load_files(files, session=name)

    @LEXPORT()
    def save_session(self):
        self.svc.save()

    @LEXPORT(in_signature='s')
    def save_session_as(self, name):
        self.svc.save_as(name)

class Sessions(Service):
    """
    Store opened buffers for later use.
    """
    options_config = SessionsOptionsConfig
    events_config = SessionsEventsConfig
    actions_config = SessionsActionsConfig
    dbus_config = SessionsDbusConfig

    def start(self):
        self._current = None
        self.datafile = get_plugin_global_settings_path('sessions', 
                                                        filename="list.json")
        self.data = {}

    def load_data(self):
        try:
            with open(self.datafile, "r") as fp:
                self.data = simplejson.load(fp)
        except IOError, e:
            self.data = {}

    def save_data(self):
        with open(self.datafile, "w") as fp:
            simplejson.dump(self.data, fp)


    def load_session(self):
        self.load_data()
        if not hasattr(self, '_session'):
            self._session = SessionWindow(self)
            self._session.set_transient_for(self.boss.window)
        #session.set_parent(self.boss.window)
        self._session.show_all()
        self._session.update_sessions()

    def save(self):
        self.save_as(self._current)

    def save_as(self, name=None):
        if not name:
            opts = DialogOptions().add('name', label=_("Session name"), 
                                       value="")
            create_gtk_dialog(opts, parent=self.boss.window).run()
            name = opts.name
        if name:
            self._current = name
            documents = self.boss.cmd('buffer', 'get_documents')
            self.data[name] = [d.filename for d in documents.values() 
                               if d.filename]
            self.save_data()

    def load_files(self):
        if self.opt('load_last_files'):
            self.load_buffers(self.opt('open_files'))

    def save_files(self, document=None):
        documents = self.boss.cmd('buffer', 'get_documents')
        files = [d.filename for d in documents.values() if d.filename]
        self.set_opt('open_files', files)

    def load_buffers(self, files, session=None):
        """
        load each file in into the buffer manager
        """
        if session:
            self._current = session
        if files:
            if self.opt('close_files_on_load'):
                self.boss.cmd('buffer', 'close_all')
            self.boss.cmd('buffer', 'open_files', files=files)
    
    def on_document_exception(self, error):
        if error.document.filename in self.opt('open_files'):
            nv = self.opt('open_files')
            nv.remove(error.document.filename)
            self.set_opt('open_files', nv)

Service = Sessions


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
