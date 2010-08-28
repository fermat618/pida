# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# stdlib
import sys, compiler, os.path, keyword, re

# gtk
import gtk

# PIDA Imports

# core
{% if languageservice %}
from pida.core.languages import LanguageService
{% else %}
from pida.core.service import Service
{% endif %}
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import (ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, 
                               TYPE_RADIO, TYPE_TOGGLE)
from pida.core.options import OptionsConfig
from pida.core.pdbus import DbusConfig


# locale
from pida.core.locale import Locale
locale = Locale('{{plugin}}')
_ = locale.gettext


class {{classname}}EventsConfig(EventsConfig):

    def create(self):
        #self.publish('something')
        pass

    def subscribe_all_foreign(self):
        #self.subscribe_foreign('buffer', 'document-changed',
        #            self.on_document_changed)
        pass

    def on_document_changed(self, document):
        pass


class {{classname}}FeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        pass


class {{classname}}OptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'configname',
            _('Short name'),
            str, # type of variable, like int, str, bool, ..
            'Skeleton',
            _('Longer description'),
        )


class {{classname}}ActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'actionname',
            TYPE_NORMAL,
            _('label'),
            _('tooltip'),
            gtk.STOCK_EXECUTE,
            self.on_example_execute,
            # '<ctrl>m'  # default shortcut or '' to enable shortcut for action
        )

    def on_example_execute(self, action):
        #self.svc.execute_current_document()
        pass

{% if languageservice %}


class {{classname}}Outliner(Outliner):

    priority = LANG_PRIO.DEFAULT
    name = "{{name}}"
    plugin = "{{name}}"
    description = _("A good description")


    filter_type = (LANG_OUTLINER_TYPES.IMPORT,
                    LANG_OUTLINER_TYPES.BUILTIN,
                    LANG_OUTLINER_TYPES.METHOD,
                    LANG_OUTLINER_TYPES.FUNCTION,
                    LANG_OUTLINER_TYPES.PROPERTY,
                    LANG_OUTLINER_TYPES.ATTRIBUTE,
                    LANG_OUTLINER_TYPES.SUPERMETHOD,
                    )

    def get_outline(self):
        for node in []:
                yield OutlineItem()


class {{classname}}Documentator(Documentator):

    name = "{{name}}"
    plugin = "{{name}}"
    description = _("Some good description")


    def get_documentation(self, buffer, offset):
        rv = Documentation(
            short='short description',
            long_='long description'
            )
        return rv
        
class {{classname}}Language(LanguageInfo):
    varchars = [chr(x) for x in xrange(97, 122)] + \
               [chr(x) for x in xrange(65, 90)] + \
               [chr(x) for x in xrange(48, 58)] + \
               ['_',]
    word = varchars

    # . in python
    attributerefs = ['.']

class {{classname}}Error(ValidationError):
    def get_markup(self):
        args = [('<b>%s</b>' % arg) for arg in self.message_args]
        message_string = self.message % tuple(args)
        if self.type_ == LANG_VALIDATOR_TYPES.ERROR:
            typec = self.lookup_color('pida-val-error')
        elif self.type_ == LANG_VALIDATOR_TYPES.INFO:
            typec = self.lookup_color('pida-val-info')
        elif self.type_ == LANG_VALIDATOR_TYPES.WARNING:
            typec = self.lookup_color('pida-val-warning')
        else:
            typec = self.lookup_color('pida-val-def')
        
        if typec:
            typec = typec.to_string()
        else:
            typec = "black"
        
        linecolor = self.lookup_color('pida-lineno')
        if linecolor:
            linecolor = linecolor.to_string()
        else:
            linecolor = "black"
        
        markup = ("""<tt><span color="%(linecolor)s">%(lineno)s</span> </tt>"""
    """<span foreground="%(typec)s" style="italic" weight="bold">%(type)s</span"""
    """>:<span style="italic">%(subtype)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno, 
                      'type':_(LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize()),
                      'subtype':_(LANG_VALIDATOR_SUBTYPES.whatis(
                                    self.subtype).capitalize()),
                      'message':message_string,
                      'linecolor': linecolor,
                      'typec': typec,
                      })
        return markup
    markup = property(get_markup)

class {{classname}}Validator(Validator):

    priority = LANG_PRIO.GOOD
    name = "{{name}}"
    plugin = "{{name}}"
    description = _("Some good description")

    def get_validations(self):
        for m in []:
            ve = {{classname}}Error(
                message=m.message,
                message_args=m.message_args,
                lineno=m.lineno,
                type_=type_,
                subtype=subtype,
                filename=filename
                )
            yield ve


class {{classname}}Completer(Completer):

    priority = LANG_PRIO.GOOD
    name = "{{name}}"
    plugin = "{{name}}"
    description = _("Creates very exact suggestions at reasonable speed")

    def get_completions(self, base, buffer, offset):

        rv = []
        for c in []:
            if c.name.startswith(base):
                r = Suggestion(c)
                rv.append(r)
        return rv


class {{classname}}Definer(Definer):

    name = "{{name}}"
    plugin = "{{name}}"
    description = _("Some good description")
    priority = LANG_PRIO.DEFAULT

    def get_definition(self, buffer, offset):
        return Definition(file_name=file_name, offset=dl.offset,
                        line=dl.lineno, length=(dl.region[1]-dl.region[0]))

{% endif %}


class {{classname}}({% if languageservice %}LanguageService{% else %}Service{%endif%}):

    features_config = {{classname}}FeaturesConfig
    actions_config = {{classname}}ActionsConfig
    options_config = {{classname}}OptionsConfig
    events_config = {{classname}}EventsConfig
{% if languageservice %}
    language_name = ({% for i in language_names%}i,{%endfor%})
    language_info = {{classname}}Language
    outliner_factory = {{classname}}Outliner
    validator_factory = {{classname}}Validator
    completer_factory = {{classname}}Completer
    definer_factory = {{classname}}Definer
    documentator_factory = {{classname}}Documentator
{% endif %}

    def pre_start(self):
        pass

    def start(self):
        pass

    def stop(self):
        # it is important to call the super stop methode
        super({{classname}}, self).stop()
        pass


# Required Service attribute for service loading
Service = {{classname}}



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
