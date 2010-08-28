# -*- coding: utf-8 -*- 
"""
    filesearch.search
    ~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Benjamin Wiegand.
    :license: GNU GPL, see LICENSE for more details.
"""

import cgi

from os import walk, path

from pida.services.filemanager.filemanager import state_style, state_text
from pida.core.environment import on_windows

from filters import filter_list


class SearchMatch(object):
    """
    Symbolizes a file that matched all search filters.
    You can add it directly to a ``kiwi.ObjectList`` object.
    """
    def __init__(self, dirpath, name, manager=None):
        self.state = 'normal'
        self.name = name
        self.path = dirpath
        self.manager = manager
        self.visible = False
        self.extension = path.splitext(self.name)[-1]
        self.icon_stock_id = self.get_icon_stock_id()

    def __repr__(self):
        return '<SearchMatch "%s">' % path.join(self.path, self.name)

    @property
    def markup(self):
        return self.format(cgi.escape(self.name))

    def get_icon_stock_id(self):
        #TODO: get a real mimetype icon
        return 'text-x-generic'

    @property
    def state_markup(self):
        text = state_text.get(self.state, ' ')
        wrap = '<span weight="ultrabold"><tt>%s</tt></span>'
        return wrap % self.format(text)

    def format(self, text):
        color, b, i = state_style.get(self.state, (None, False, False))
        if self.manager and color:
            #FIXME to_string is missing on win32
            color = self.manager.match_list.style.lookup_color(color)
            if not on_windows:
                color = color.to_string()
            else:
                color = '#%s%s%s' % (color.red,color.green,color.blue)
        else:
            color = "black"
        if b:
            text = '<b>%s</b>' % text
        if i:
            text = '<i>%s</i>' % text
        return '<span color="%s">%s</span>' % (color, text)


def get_filters():
    """
    Returns the a tuple of the filter's description and the filters itself.
    """
    return [(f.description, f) for f in filter_list]

def do_search(folder, filters, exclude_hidden=True, exclude_vcs=True):
    """
    Test all ``filters`` on ``folder``'s content recursively.
    If a file matches all filters a ``SearchMatch`` object is yielded.
    """
    for dirpath, dirnames, filenames in walk(folder):
        def _get_hidden(dirnames):
            """
            Return the directories that shouldn't be shown.
            """
            hidden = []
            for dirname in dirnames:
                if dirname.startswith('.'):
                    hidden.append(dirname)
            return hidden

        if exclude_hidden:
            # remove the hidden folders of ``dirnames`` that they don't get
            # crawled
            for dirname in _get_hidden(dirnames):
                # XXX: Check whether removing using .pop with index is faster
                dirnames.remove(dirname)

        for file_name in filenames:
            fpath = path.join(dirpath, file_name)
            errors = False

            if not path.exists(fpath):
                # this may happen if there's a invalid symlink
                continue

            for f in filters:
                if not f.check(fpath):
                    # file doesn't matches filter
                    errors = True
                    break

            if not errors:
                # file did match all filters
                yield dirpath, file_name
