# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import icons

from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.objectlist import ObjectList, ObjectTree


### Monkey Patching

from pida.ui.objectlist import sort_by_attribute

if not hasattr(ObjectList, 'sort_by_attribute'):
    ObjectList.sort_by_attribute = sort_by_attribute
