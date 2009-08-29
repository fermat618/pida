# -*- coding: utf-8 -*-

# stdlib imports
from collections import defaultdict

# PIDA imports
from pida.core.service import Service
from pida.core.languages import LanguageService, Outliner
from pida.utils.languages import OutlineItem, LANG_OUTLINER_TYPES, LANG_PRIO
from pida.utils.addtypes import Enumeration
from pida.services.language import DOCTYPES

# docutils imports
from docutils import nodes
from docutils.core import publish_doctree


class RSTTokenList(object):

    def __init__(self):
        self._items = defaultdict(list)
        self._names = defaultdict(dict)

    def add(self, item):
        self._items[item.filename].append(item)
        self._names[item.filename][item.name] = item

    def filter_items(self, filename):
        for i in self._items[filename]:
            if not i.parent and i.parent_name:
                i.parent = self.get_parent(i)
            yield i

    def clear(self):
        self._items.clear()
        self._names.clear()

    def clear_filename(self, filename):
        del self._items[filename]
        del self._names[filename]

    def get_parent(self, item):
        if item.parent:
            return item.parent
        return self._names[item.filename].get(item.parent_name, None)

    def __iter__(self):
        for j in self._items.itervalues():
            for i in j:
                if not i.parent and i.parent_name:
                    i.parent = self._names[i.filename].get(i.parent_name, None)
                yield i


class RSTItem(OutlineItem):

    def _get_fullname(self):
        if not self.parent_name:
            return self.name
        return "%s.%s" %(self.parent_name, self.name)
    fullname = property(_get_fullname)

    def __repr__(self):
        return "<RSTItem %s %s %s>" % \
                            (self.name, self.parent_name, self.fullname)


class RSTOutliner(Outliner):

    name = "rst"
    plugin = "rst"
    description = _("An outliner for ReStructuredText")

    section_types = (LANG_OUTLINER_TYPES.SECTION,
                     LANG_OUTLINER_TYPES.PARAGRAPH)

    def get_outline(self):
        if not self.document.filename:
            return
        self.doc_items = RSTTokenList()
        self._parse_rst(self.document.filename)
        # TODO: check if this really *does* anything
        if self.document.project:
            self.document.project['rst_cache'] = self.doc_items
        for item in self.doc_items:
            yield item

    def _recursive_node_walker(self, node, level, parent_name):
        try:
            new_item = False
            next_parent_name = parent_name
            item_kwargs = {}
            if isinstance(node, nodes.section):
                new_item = True
                name = \
                    str(node.astext().partition(node.child_text_separator)[0])
                type = (self.section_types[level]
                            if level < len(self.section_types)
                            else self.section_types[-1])
                is_container = True
                # increase level and set parent for next section
                level += 1
                next_parent_name = name
            elif (isinstance(node, nodes.image) or
                  isinstance(node, nodes.figure)):
                new_item = True
                name = node.attributes['uri']
                type = LANG_OUTLINER_TYPES.UNKNOWN
                is_container = False
                item_kwargs = {'icon_name': 'source-image'}
        except:
            print "Exception while parsing node info; node ignored"
            pass # ignore node if *something goes wrong
        else:
            if new_item:
                item = RSTItem(name=name,
                               filename=node.source,
                               linenumber=node.line - 1,
                               type=type,
                               filter_type=type,
                               is_container=is_container,
                               parent_name=parent_name,
                               **item_kwargs)
                self.doc_items.add(item)

        if len(node.children):
            for child in node:
                self._recursive_node_walker(child, level, next_parent_name)

    def _parse_rst(self, filename):
        """Use docutils to parse the rst file and save interesting items
           as RTSItem instances.
        """
        f = open(filename)
        rst_data = f.read()
        doctree = publish_doctree(rst_data)
        f.close()
        self._recursive_node_walker(doctree, 0, None)


class RST(LanguageService):

    language_name = (DOCTYPES.get_fuzzy('reStructuredText')).internal
    outliner_factory = RSTOutliner

# Required Service attribute for service loading
Service = RST

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
