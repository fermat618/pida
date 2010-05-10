# -*- coding: utf-8 -*-

from __future__ import with_statement

# stdlib imports
import os
import sys
import pickle
import textwrap
import pida.utils.serialize as simplejson
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
    # TODO importing Sphinx will automatically register all Sphinx
    # specific directives and roles within the already imported docutils
    # and therefor has side effects even if it's not used afterwards.
    # It might be a better idea to import only if the usage of Sphinx has
    # been configured.
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment as SphinxBuildEnvironment
    from sphinx.config import Config as SphinxConfig
    sphinx_available = True
except ImportError:
    sphinx_available = False

# --- common plugin code ------------------------------------------------------

class RSTPlugin(object):

    def __init__(self, service):
        self.config = {'sphinx' : False,
                       'basedir': '',
                       'builddir': ''}
        self.load(service)
        if self.config['sphinx']:
            self.set_up_sphinx(service)

    def save(self, service):
        # TODO: not used yet, GUI for config?
        pro = service.boss.cmd('project', 'get_current_project')
        if not pro:
            return
        else:
            datadir = pro.get_meta_dir('rst')
            datafile = os.path.join(datadir, 'rst.json')
        try:
            fp = open(datafile, "w")
            simplejson.dump(self.config, fp, indent=1)
        except Exception, e:
            service.log.exception(e)

    def load(self, service):
        pro = service.boss.cmd('project', 'get_current_project')
        if not pro:
            return
        datadir = pro.get_meta_dir('rst')
        datafile = os.path.join(datadir, 'rst.json')
        if os.path.isfile(datafile):
            try:
                fp = open(datafile, "r")
                self.config = simplejson.load(fp)
            except Exception, e:
                service.log.exception(e)

    @staticmethod
    def _do_nothing(*args, **kwargs):
        pass

    def set_up_sphinx(self, service):
        """Create a Sphinx application. This registers all extension roles and
        directives in docutils.
        """
        try:
            srcdir = self.config['basedir']
            confdir = self.config['basedir']
            outdir = os.path.join(srcdir, self.config['builddir'])
            doctreedir = os.path.join(outdir, 'doctrees')
            buildername = "html" # does not really matter
            confoverrides = {}
            status = sys.stdout
            warning = sys.stderr # TODO catch and display in PIDA context!
            self.sphinx = Sphinx(srcdir, confdir, outdir, doctreedir,
                            buildername, confoverrides, status, warning,
                            freshenv=False, warningiserror=False, tags=None)
            # overwrite some builder methods to prevent actual output production
            self.sphinx.builder.write = self._do_nothing
            self.sphinx.builder.finish = self._do_nothing
            self.sphinx.builder.cleanup = self._do_nothing
        except Exception, e:
            service.log.exception()  # TODO: hint that Sphinx config is invalid

    def create_sphinx_env(self):
        """trigger the creation of the pickled environment and *all* pickled
           doctrees.
        """
        self.sphinx.build(True, '')

    # TODO: currently the Validator and the Outliner call this function and
    # parse the complete rst file. Caching the doctree would be cool but I have
    # no idea how to do that since they are running in different processes (?)
    def parse_rst(self, document, sphinx_env = False):
        """Parse the rst file and return the doctree. Parsing is be done by
           using one of the following three methods:

           1. plain docutils
           2. docutils witch some Sphinx specific settings
           3. using a pickled doctree from a full Sphinx build.
        """

        def plain_docutils(filename):
            """Use plain docutils method for generating the doctree. No Sphinx
               specific markup has been registered.
            """
            return publish_doctree(rst_data, source_path = filename)

        def sphinx_docutils(filename):
            """Use docutils function to generate the doctree. If
               :func:`set_up_sphinx()` has been called during initialization
               all Sphinx specific markup including extensions have
               been registered in docutils. Otherwise, extension specific
               markup is missing.

               Note that this code is a bit fragile since no official Sphinx
               API is used.
            """
            config = SphinxConfig (None, None, None, None)
            env = SphinxBuildEnvironment (os.path.dirname(filename), "", config)
            env.docname = filename
            env.found_docs = set([filename])
            settings_overrides = {'env': env}
            return publish_doctree(rst_data, source_path = filename,
                                   settings_overrides = {'env': env})

        def sphinx_full(filename):
            """Load a pickled doctree (created by a full sphinx build) from
               disk.
            """
            srcdir = self.config['basedir']
            outdir = os.path.join(srcdir, self.config['builddir'])
            doctreedir = os.path.join(outdir, 'doctrees')
            doctreefile = os.path.join (doctreedir,
                                        "%s.doctree" % os.path.splitext
                                        (os.path.relpath(filename, srcdir))[0])
            if os.path.isfile(doctreefile):
                with open(doctreefile) as f:
                    doctree = pickle.load(f)
            else:
                # rst file within the sphinx project but not included in any
                # doctree. Fall back.
                doctree = sphinx_docutils(filename)
            return doctree

        doctree = None
        with open(document.filename) as f:
            rst_data = f.read()
        if not sphinx_available:
            doctree = plain_docutils(document.filename)
        elif not self.config['sphinx']:
            doctree = sphinx_docutils(document.filename)
        else:
            if sphinx_env:
                # TODO: This will give better results (toctree is resolved, ...)
                # but I think there are race conditions if both the outliner
                # and the validator are activated.
                # TODO: loading all doctrees and displaying the *full* structure
                # of a complete Sphinx project in the Outliner would be a cool
                # feature.
                self.create_sphinx_env()
                doctree = sphinx_full(document.filename)
            else:
                doctree = sphinx_docutils(document.filename)
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
    @property
    def fullname(self):
        if not self.parent_name:
            return self.name
        return "%s.%s" %(self.parent_name, self.name)

    def __repr__(self):
        return "<RSTItem %s %s %s>" % \
                            (self.name, self.parent_name, self.fullname)
    @property
    def markup(self):
        return ('<b>%s</b> <span foreground="#999999"><i>%s%s</i></span>'
                % (self.name,
                  (self.filename + ':') if self.external else '',
                  self.linenumber))

class RSTOutliner(Outliner):

    priority = LANG_PRIO.VERY_GOOD
    plugin = "rst"
    name = "rst outliner"
    description = _("An outliner for ReStructuredText")

    section_types = (LANG_OUTLINER_TYPES.SECTION,
                     LANG_OUTLINER_TYPES.PARAGRAPH)

    def get_outline(self):
        self.doc_items = RSTTokenList()
        self.rstplugin = RSTPlugin(self.svc)
        self.doctree = self.rstplugin.parse_rst(self.document)
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
        except Exception, e:
            pass # ignore node if *something* goes wrong
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
        self.rstplugin = RSTPlugin(self.svc)
        self.doctree = self.rstplugin.parse_rst(self.document)
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

class Service(LanguageService):

    language_name = (DOCTYPES.get_fuzzy('reStructuredText')).internal
    outliner_factory = RSTOutliner
    validator_factory = RSTValidator

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
