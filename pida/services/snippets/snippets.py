# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
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
