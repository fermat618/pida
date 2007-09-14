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

    def __init__(self):
        """

        """

    def validate(self):
        """

        """

    @staticmethod
    def get_entries():
        """

        """

    def check(self, path):
        """

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


class ContentContainsFilter(Filter):
    """
    Checks whether the file contains a given text.
    """
    description = _('Contains the text')

    def __init__(self, entry):
        self.entry = entry

    def validate(self):
        self.text = self.entry.get_text()

    @staticmethod
    def get_entries():
        return {
            'entry': gtk.Entry()
        }

    def check(self, path):
        f = file(path)
        found = False

        for line in f.readlines():
            if self.text in line:
                found = True
                break

        f.close()

        return found


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


filter_list = [FileNameMatchesFilter, ContentContainsFilter,
               ContentMatchesFilter]
