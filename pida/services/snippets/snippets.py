# -*- coding: utf-8 -*- 
"""
    Sessions Service
    ~~~~~~~~~~~~~~~~

    currently this saves the open files to a gconf list

    .. todo::
        * window/sudebar/paned positions

    :license: GPL2 or later
    :copyright:
        * 2007 Ali Afshar
        * 2008 Ronny Pfannschmidt
"""


# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
#from pida.core.options import OptionsConfig, manager
from pida.core.pdbus import DbusConfig, EXPORT

# locale
from pida.core.locale import Locale
locale = Locale('sessions')
_ = locale.gettext

#
# class SessionsOptionsConfig(OptionsConfig):
#
#     def create_options(self):
#         self.create_option(
#             'open_session_manager',
#             _('Always show session manager'),
#             bool,
#             True,
#             _('Always open the session manager when no session name is given'),
#         )
#
#         self.create_option(
#             'load_last_files',
#             _('Load last opened files on startup'),
#             bool,
#             True,
#             _('Load last opened files on startup'),
#             session=True
#         )
#
#         self.create_option(
#             'open_files',
#             _('Open Files'),
#             list,
#             [],
#             _('The list of open files'),
#             safe=False,
#             session=True
#             )
#
#     gladefile = 'sessions-properties'
#     label_text = _('Sessions Properties')
#     icon_name = 'package_utilities'
#
# class SessionsEventsConfig(EventsConfig):
#
#     def subscribe_all_foreign(self):    
#         self.subscribe_foreign('buffer', 'document-closed', self.svc.save_files)
#         self.subscribe_foreign('buffer', 'document-changed', self.svc.save_files)
#         self.subscribe_foreign('editor', 'started', self.svc.load_files)
#         self.subscribe_foreign('editor', 'document-exception', self.svc.on_document_exception)
#


class TabStop(object):
    pass

class TextToken(unicode):
    pass

class VariableToken(object):
    default = ""
    required = False

class SnippetTemplate(object):
    text = ""

    def get_template(self):
        """
        Return text for inclusion.
        This may need expanding the template.
        """
        return self.text

    def get_tokens(self):
        """
        Returns a list of Text and Template Tokens
        """
        return [TextToken(self.text)]


class SnippetsEventsConfig(EventsConfig):
    def create(self):
        self.publish('registered', 'unregistered')

class SnippetsDbus(DbusConfig):

#     @EXPORT(out_signature='as')
#     def get_session_name(self):
#         return []
#         #return manager.session
    pass

class SnippetsProvider(object):

    def get_snippets(self, document):
        raise NotImplemented

class Snippets(Service):
    """
    Store opened buffers for later use.
    """
    options_config = SnippetsEventsConfig
    events_config = SnippetsEventsConfig
    dbus_config = SnippetsDbus

    def pre_start(self):
        self._providers = []

    def get_snippets(self, document, offset=-1, base=""):
        """
        Returns a list of snippets for this document
        """
        for prov in self._providers:
            for snip in prov.get_snippets(document,
                offset=offset, base=base):
                if snip:
                    yield snip

    def list_providers(self):
        return self._providers[:]

    def register_provider(self, provider):
        if provider not in self._providers:
            self._providers.append(provider)
            self.emit('registered', provider)
    
    def unregister_provider(self, provider):
        if provider in self._providers:
            self._providers.remove(provider)
            self.emit('unregistered', provider)

Service = Snippets


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
