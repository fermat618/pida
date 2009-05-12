# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
The disable language service

These are noop language services that can be moved upwards in the prio list
to disable language support for a specific language but do nothing

:license: GPL2 or later
:copyright: 2008 the Pida Project
"""

from pida.core.languages import (Outliner, Completer, Validator, Documentator, 
                                Definer)

# locale
from pida.core.locale import Locale
locale = Locale('core')
_ = locale.gettext

#FIXME: maybe we should fill the plugin values with a metaclass ???
# class LanguageMetaclass(type):
#     def __new__(meta, name, bases, dct):
#         print "Creating class %s using CustomMetaclass" % name
#         print meta, name, bases, dct
#         klass = type.__new__(meta, name, bases, dct)
#         #meta.addParentContent(klass)
#         klass.plugin = dct['__module__']
#         return klass

class NoopBase(object):
    name = _("Disabled")
    priority = -1000
    plugin = "language"
    description = _("Disables the functionality")
    IS_DISABELING = True


class NoopOutliner(NoopBase, Outliner):
    """
    Noop outliner
    """
    def get_outline(self):
        return []


class NoopValidator(NoopBase, Validator):
    """
    Noop validator
    """
    name = _("Disabled")

    def get_validations(self):
        return []

class NoopDefiner(NoopBase, Definer):
    """
    Noop definer
    """
    def get_definition(self, buffer, offset):
        """
        returns None
        """
        return None

class NoopDocumentator(NoopBase, Documentator):
    """
    Documentation receiver returns a Documentation object
    """

    def get_documentation(self, buffer, offset):
        """
        return None
        """
        return None


class NoopCompleter(NoopBase, Completer):

    def get_completions(self, base, buffer_, offset):
        """
        Gets a list of completitions.
        
        @base - string which starts completions
        @buffer - document to parse
        @offset - cursor position
        """
        return []


