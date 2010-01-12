# -*- coding: utf-8 -*-

from __future__ import with_statement

# stdlib imports
import textwrap
import os
from collections import defaultdict

# PIDA imports
from pida.core.languages import LanguageService, Outliner, Validator
from pida.utils.languages import (LANG_PRIO,
    LANG_OUTLINER_TYPES, OutlineItem,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, ValidationError)
from pida.services.language import DOCTYPES

# docutils imports
from docutils import nodes
from docutils.core import publish_doctree

# Sphinx imports
try:
    # importing the BuildEnvironment will automatically register all Sphinx
    # specific directives and roles within the already imported docutils.
    from sphinx.environment import BuildEnvironment as SphinxBuildEnvironment
    from sphinx.config import Config as SphinxConfig
    sphinx_available = True
except ImportError:
    sphinx_available = False

if sphinx_available:
# TODO figure out which Sphinx config to use. This is important since we have
# to enable all necessary extensions. First check if the configuration
# specifies a conf.py otherwise travel up the directory hierarchy (max to the
# project root directory) to find it.
    #use_sphinx = within_sphinx_environment():
    use_sphinx = True;
# TODO config option to deactive Sphinx (for performance)
# elif conf.do_not_use_sphinx:
#     use_sphinx = False
else:
    use_sphinx = False


# --- common plugin code ------------------------------------------------------

# TODO: currently the Validator and the Outliner call this function and parse
# the complete rst file. Caching the doctree would be cool!
def parse_rst(document):
    """
    Use docutils to parse the rst file and return the doctree.
    """
    with open(document.filename) as f:
        rst_data = f.read()
    settings_overrides = None
    if use_sphinx:
        config = SphinxConfig (None, None, None, None)
        env = SphinxBuildEnvironment (os.path.dirname(document.filename),
                                      "", config)
        # make toctree directive happy (sphinx/directives/other.py)
        env.docname = document.filename
        env.found_docs = set([document.filename])
        settings_overrides = {'env': env}

        # Using the Sphinx mechanism to save a pickled doctree to disc
        # will speed up a subsequent build but since saving the document is
        # most probably done more often than building we do not use this
        # caching method. Or should we? See BuildEnvironment.read_doc()

    doctree = publish_doctree(rst_data,
                              source_path = document.filename,
                              settings_overrides = settings_overrides)
    return doctree

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

    def get_markup(self):
        return ('<b>%s</b> <span foreground="#999999"><i>%s%s</i></span>'
                % (self.name,
                  (self.filename + ':') if self.external else '',
                  self.linenumber))
    markup = property(get_markup)

class RSTOutliner(Outliner):

    priority = LANG_PRIO.VERY_GOOD
    plugin = "rst"
    name = "rst outliner"
    description = _("An outliner for ReStructuredText")

    section_types = (LANG_OUTLINER_TYPES.SECTION,
                     LANG_OUTLINER_TYPES.PARAGRAPH)

    def get_outline(self):
        self.doc_items = RSTTokenList()
        self.doctree = parse_rst(self.document)
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
                               linenumber=str(linenumber),
                               type=type,
                               filter_type=type,
                               is_container=is_container,
                               parent_name=parent_name,
                               external=node.source != self.document.filename,
                               **item_kwargs)
                self.doc_items.add(item)

        if len(node.children):
            for child in node:
                self._recursive_node_walker(child, level, next_parent_name)

# --- Validator ---------------------------------------------------------------

class RSTValidator(Validator):

    priority = LANG_PRIO.VERY_GOOD
    plugin = "rst"
    name = "rst validator"
    description = _("A validator for ReStructuredText")

    subtype = LANG_VALIDATOR_SUBTYPES.SYNTAX

    def get_validations(self):
        self.doctree = parse_rst(self.document)
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

class Service(LanguageService):

    language_name = (DOCTYPES.get_fuzzy('reStructuredText')).internal
    outliner_factory = RSTOutliner
    validator_factory = RSTValidator

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
