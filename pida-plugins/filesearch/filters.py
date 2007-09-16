# -*- coding: utf-8 -*- 
"""
    filesearch.filters
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Benjamin Wiegand.
    :license: GNU GPL, see LICENSE for more details.
"""

import re
import gtk
import sre_constants

from glob import fnmatch
from os.path import basename

from pida.core.locale import Locale
locale = Locale('filesearch')
_ = locale.gettext

BINARY_RE = re.compile(r'[\000-\010\013\014\016-\037\200-\377]|\\x00')


class ValidationError(Exception):
    """
    An exception that is raised if the user entered invalid data into a
    filter's field.
    The search catches it and informs the user.
    """


class Filter(object):
    """
    A search filter that lowers the search result.
    """

    #: The description of the filter
    filter_desc = ''

    @staticmethod
    def get_entries():
        """
        This method should return a dictionary containing all input elements
        the filter needs.
        Example::

            return {
                'entry': gtk.Entry()
            }
        """

    def __init__(self):
        """
        The init function is called if the user added a new filter.
        It get's all input elements defined in ``get_entries`` as keyword
        arguments.
        """

    def validate(self):
        """
        This function is called before the search process starts.
        It should validate all input elements and raise a ``ValidationError``
        on error.
        """

    def check(self, path):
        """
        This function should return ``True`` if ``path`` matches the filter,
        else ``False``.
        """


class FileNameMatchesFilter(Filter):
    """
    Checks whether the file name matches a given regular expression.
    """
    description = _('Name matches')

    def __init__(self, entry):
        self.entry = entry

    def validate(self):
        pattern = self.entry.get_text()
        pattern = fnmatch.translate(pattern).rstrip('$')
        try:
            self.regex = re.compile(pattern, re.IGNORECASE)
        except sre_constants.error, e:
            raise ValidationError(_('Invalid Regex'))

    @staticmethod
    def get_entries():
        return {
            'entry': gtk.Entry()
        }

    def check(self, path):
        return bool(self.regex.search(basename(path)))


class ContentMatchesFilter(Filter):
    """
    Checks whether the file content matches a given regular expression.
    """
    description = _('Content matches')

    def __init__(self, entry):
        self.entry = entry

    def validate(self):
        pattern = self.entry.get_text()
        pattern = fnmatch.translate(pattern).rstrip('$')
        try:
            self.regex = re.compile(pattern, re.IGNORECASE)
        except sre_constants.error, e:
            raise ValidationError(_('Invalid Regex'))

    @staticmethod
    def get_entries():
        return {
            'entry': gtk.Entry()
        }

    def check(self, path):
        f = file(path)
        found = False

        for line in f.readlines():
            if BINARY_RE.search(line):
                # binary file, abort
                break

            if self.regex.search(line):
                found = True
                break

        f.close()
        return found


filter_list = [FileNameMatchesFilter, ContentMatchesFilter]
