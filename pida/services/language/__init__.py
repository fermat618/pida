# -*- coding: utf-8 -*- 
"""
    pida.services.languages
    ~~~~~~~~~~~~~~~~~~~~~

    Supplies support for languages

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL2 or later
"""

from pida.core.doctype import TypeManager

DOCTYPES = TypeManager()
from .deflang import DEFMAPPING
DOCTYPES._parse_map(DEFMAPPING)
