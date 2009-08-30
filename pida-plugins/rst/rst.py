# -*- coding: utf-8 -*-

# stdlib imports
import textwrap
from collections import defaultdict

# PIDA imports
from pida.core.service import Service
from pida.core.languages import LanguageService, Outliner, Validator
from pida.utils.languages import (LANG_PRIO,
    LANG_OUTLINER_TYPES, OutlineItem,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, ValidationError)
from pida.utils.addtypes import Enumeration
from pida.services.language import DOCTYPES

# docutils imports
from docutils import nodes
from docutils.core import publish_doctree

# --- common plugin code ------------------------------------------------------

class RST(object):

    def _parse_rst(self, filename):
        """Use docutils to parse the rst file and save the doctree.
        """
        self.doctree = None

        f = open(filename)
        rst_data = f.read()
        self.doctree = publish_doctree(rst_data)
        f.close()

        # TODO caching!!!
        #if self.document.project:
        #    self.document.project['rst_cache'] = self.doctree ??


# --- Outliner support --------------------------------------------------------

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


class RSTOutliner(Outliner, RST):

    priority = LANG_PRIO.VERY_GOOD
    plugin = "rst"
    name = "rst outliner"
    description = _("An outliner for ReStructuredText")

    section_types = (LANG_OUTLINER_TYPES.SECTION,
                     LANG_OUTLINER_TYPES.PARAGRAPH)

    def get_outline(self):
        self.doc_items = RSTTokenList()
        self._parse_rst(self.document.filename)
        if self.doctree:
            self._recursive_node_walker(self.doctree, 0, None)
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
                linenumber = node.line - 1
                # increase level and set parent for next section
                level += 1
                next_parent_name = name
            elif (isinstance(node, nodes.image) or
                  isinstance(node, nodes.figure)):
                new_item = True
                name = node.attributes['uri']
                type = LANG_OUTLINER_TYPES.UNKNOWN
                is_container = False
                # nodes with options have no line attribute
                linenumber = node.line or node.parent.line
                item_kwargs = {'icon_name': 'source-image'}
        except:
            pass # ignore node if *something goes wrong
        else:
            if new_item:
                item = RSTItem(name=name,
                               filename=node.source,
                               linenumber=linenumber,
                               type=type,
                               filter_type=type,
                               is_container=is_container,
                               parent_name=parent_name,
                               **item_kwargs)
                self.doc_items.add(item)

        if len(node.children):
            for child in node:
                self._recursive_node_walker(child, level, next_parent_name)

# --- Validator ---------------------------------------------------------------

class RSTValidator(Validator, RST):

    priority = LANG_PRIO.VERY_GOOD
    plugin = "rst"
    name = "rst validator"
    description = _("A validator for ReStructuredText")

    subtype = LANG_VALIDATOR_SUBTYPES.SYNTAX

    def get_validations(self):
        self._parse_rst(self.document.filename)
        if self.doctree:
            for msg in self.doctree.parse_messages :
                message, type_, filename, lineno = self._parse_error(msg)
                # TODO need to filter out duplicates with no lineno set
                # not sure why this happens...
                if lineno:
                    yield ValidationError (message=message,
                                           type_=type_,
                                           subtype=self.subtype,
                                           filename=filename,
                                           lineno=lineno)

    @staticmethod
    def _parse_error(msg):
        width = 30  # TODO make configurable?
        message = textwrap.fill(msg.children[0].children[0].data, width)
        # docutils defines the following error levels:
        #     "info/1", '"warning"/"2" (default), "error"/"3", "severe"/"4"
        type_ = (LANG_VALIDATOR_TYPES.INFO, LANG_VALIDATOR_TYPES.WARNING,
                 LANG_VALIDATOR_TYPES.ERROR, LANG_VALIDATOR_TYPES.FATAL
                )[msg['level'] - 1]
        filename = msg.source
        lineno = msg.line
        return (message, type_, filename, lineno)

# --- register plugin services ------------------------------------------------

class RSTService(LanguageService):

    language_name = (DOCTYPES.get_fuzzy('reStructuredText')).internal
    outliner_factory = RSTOutliner
    validator_factory = RSTValidator

# Required Service attribute for service loading
Service = RSTService

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
