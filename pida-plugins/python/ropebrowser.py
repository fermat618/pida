

"""
Rope integration for PIDA.

Rope is an all-round python analysis/refactoring library.

http://rope.sourceforge.net
"""

from os.path import dirname, basename

from pida.core.projects import Project as PidaProject
from rope.base.project import Project, get_no_project
from rope.base import pynames, pyobjects, builtins

from pida.utils.languages import LANG_OUTLINER_TYPES, OutlineItem


def markup_italic(text):
    """Make some italic pango"""
    return '<i>%s</i>' % text

def markup_color(text, color):
    """Make some coloured pango"""
    return '<span foreground="%s">%s</span>' % (color, text)

def markup_bold(name):
    """Make some bold pango"""
    return '<b>%s</b>' % name

def markup_grey_italic(text):
    return markup_color(markup_italic(text), '#999999')

def markup_green_italic(text):
    return markup_color(markup_italic(text), '#339933')

def markup_bold_bracketted(text):
    return '%s%s%s' % (
        markup_bold('('),
        markup_italic(text),
        markup_bold('):')
    )

def markup_type(name, color):
    return markup_italic(markup_color(name, color))

def markup_location(linenumber, filename=None):
    if linenumber is None:
        s = ''
    elif filename is None:
        s = linenumber
    else:
        s = '%s:%s' % (filename, linenumber)
    return markup_grey_italic(s)

def markup_fixed(text):
    return '<tt>%s</tt>' % text

def markup_name(name):
    return markup_bold(markup_fixed(name))


class TreeOptions(object):
    """The per-type options for a source node type."""
    type_name = 'u'
    type_color = '#000000'
    position = 0
    has_children = False
    icon_name = 'source-property'
    filter_type =  LANG_OUTLINER_TYPES.UNKNOWN
    def __init__(self, treeitem):
        self.item = treeitem

    def get_extra_markup(self):
        """Markup added to the end of each definition"""
        return ''

    def get_pre_markup(self):
        """Markup prepended to the definition name"""
        return ''


class FunctionOptions(TreeOptions):
    """Describe how functions are shown"""

    type_name = 'f'
    icon_name = 'source-function'
    type_color = '#900000'
    position = 2
    filter_type = LANG_OUTLINER_TYPES.UNKNOWN

    def get_pre_markup(self):
        """Draw decorators"""
        decs = []
        for dec in self.item.object.decorators:
            if hasattr(dec, 'id'):
                decs.append('@' + dec.id)
            elif hasattr(dec, 'func') and hasattr(dec.func, 'id'):
                decs.append('@' + dec.func.id + '()')
        decs = ', '.join(decs)
        if decs:
            decs = decs + '\n'
        return markup_fixed(markup_italic(decs))


    def get_extra_markup(self):
        attrs = markup_bold_bracketted(
            ', '.join(self.item.object.get_param_names())
        )
        doc = self.item.object.get_doc()
        if doc:
            doc_markup = markup_green_italic('"""%s"""' % doc.splitlines()[0])
            attrs = attrs + '\n' + doc_markup
        return attrs


class EvaluatedOptions(TreeOptions):

    type_name = 'p'
    icon_name = 'source-property'
    type_color = '#900090'
    filter_type = LANG_OUTLINER_TYPES.PROPERTY

class MethodOptions(FunctionOptions):

    type_name = 'm'
    icon_name = 'source-method'
    filter_type = LANG_OUTLINER_TYPES.METHOD


class SuperMethodOptions(MethodOptions):

    type_name = '(m)'
    icon_name = 'source-extramethod'
    position = 6
    filter_type = LANG_OUTLINER_TYPES.SUPERMETHOD


class ClassMethodOptions(MethodOptions):

    type_name = 'cm'
    icon_name = 'source-method'
    position = 3


class StaticMethodOptions(MethodOptions):

    type_name = 'sm'
    icon_name = 'source-method'
    position = 4


class ClassOptions(TreeOptions):

    type_name = 'c'
    icon_name = 'source-class'
    type_color = '#000090'
    position = 1
    has_children = True

    def get_extra_markup(self):
        attrs = markup_bold_bracketted(
            ', '.join([s.get_name() for s in
                       self.item.object.get_superclasses() if hasattr(s, 'get_name')])
        )

        doc = self.item.object.get_doc()
        if doc:
            doc_markup = markup_green_italic('"""%s"""' % doc.splitlines()[0])
            attrs = attrs + '\n' + doc_markup
        return attrs


class AssignedOptions(TreeOptions):

    type_name = 'a'
    icon_name = 'source-attribute'
    type_color = '#009000'
    position = 5
    filter_type = LANG_OUTLINER_TYPES.ATTRIBUTE


class BuiltinOptions(TreeOptions):

    type_name = '(b)'
    icon_name = None
    type_color = '#999999'
    position = 7
    filter_type = LANG_OUTLINER_TYPES.BUILTIN


class ImportedOptions(TreeOptions):

    type_name = 'imp'
    icon_name = 'source-import'
    type_color = '#999999'
    position = 8
    filter_type = LANG_OUTLINER_TYPES.IMPORT


def get_option_for_item(item):
    if isinstance(item.node, pynames.ImportedName):
        return ImportedOptions(item)
    elif isinstance(item.node, pynames.ImportedModule):
        return ImportedOptions(item)
    elif isinstance(item.node, pynames.DefinedName):
        if isinstance(item.object, pyobjects.PyFunction):
            kind = item.object.get_kind()
            if kind == 'method':
                if item.name in item.parent.object.get_scope().get_defined_names():
                    return MethodOptions(item)
                else:
                    return SuperMethodOptions(item)
            elif kind == 'classmethod':
                return ClassMethodOptions(item)
            elif kind == 'staticmethod':
                return StaticMethodOptions(item)
            else:
                return FunctionOptions(item)
        else:
            return ClassOptions(item)
    elif isinstance(item.node, pynames.AssignedName):
        return AssignedOptions(item)
    elif isinstance(item.node, builtins.BuiltinName):
        return BuiltinOptions(item)
    elif isinstance(item.node, pynames.EvaluatedName):
        return EvaluatedOptions(item)
    else:
        print 'Unknown Node', item, item.node, item.name, item.object


class SourceTreeItem(OutlineItem):

    def __init__(self, mod, name, node, parent):
        self.name = name
        self.node = node
        self.object = node.get_object()
        self.parent = parent

        # where is the thing defined
        self.def_module, self.linenumber = self.node.get_definition_location()
        self.foreign = mod is not self.def_module
        if self.foreign and self.def_module is not None:
            self.filename = self.def_module.get_resource().path
        else:
            self.filename =  None

        self.options = get_option_for_item(self)

        self.sort_hack = '%s%s' % (self.options.position, self.name)

        if self.filename:
            self.line_sort_hack = 'yyy%s%s' % (self.filename, self.linenumber)
        else:
            if not self.linenumber:
                self.line_sort_hack = 'zzz'
            else:
                self.line_sort_hack = '%s' % self.linenumber

        self.type_markup = markup_type(self.options.type_name,
                                       self.options.type_color)

        self.filter_type = self.options.filter_type
        self.icon_name = self.options.icon_name

    def get_markup(self):
        return '%s%s%s %s' % (
            self.options.get_pre_markup(),
            markup_name(self.name),
            self.options.get_extra_markup(),
            markup_location(self.linenumber, self.filename)
        )
    markup = property(get_markup)


def get_project(path):
    return Project(dirname(path), ropefolder=None), basename(path)[:-3]


class ModuleParser(object):

    def __init__(self, filename, project=None):
        self.filename = filename
        self.modname = basename(filename)[:-3]
        if project:
            if not project.has_key('python'):
                project['python'] = {}
            if not project['python'].has_key('ropeproject'):
                project['python']['ropeproject'] = Project(
                    project.source_directory, 
                    ropefolder=PidaProject.data_dir_path('', 'python'))

            self.project = project['python']['ropeproject']
            parts = project.get_relative_path_for(filename)
            self.modname = ".".join(parts)[:-3]
        else:
            self.project, self.modname = get_project(filename)
        self.mod = self.project.pycore.get_module(self.modname)

    def get_nodes(self):
        for name, node in self.mod.get_attributes().items():
            for name, node in self.create_tree_items(name, node):
                yield name, node

    def create_tree_items(self, name, node, parent=None, start=False):
        ti = SourceTreeItem(self.mod, name, node, parent)
        if ti:
            yield ti, parent
            if ti.options.has_children:
                for name, child in ti.object.get_attributes().items():
                    for node, parent in self.create_tree_items(name, child, ti):
                        if node is not None:
                            yield node, parent




def _test():
    import gtk

    mp = ModuleParser(__file__)

    def create_ui():
        from kiwi.ui.objectlist import ObjectTree, Column
        source_tree = ObjectTree()
        source_tree.set_columns(
            [
                Column('rendered', use_markup=True, expand=True),
                Column('sort_hack', visible=False, sorted=True),
            ]
        )
        source_tree.set_headers_visible(False)
        return source_tree

    w = gtk.Window()
    ol = create_ui()
    w.add(ol)
    w.show_all()

    for n, p in mp.get_nodes():
        ol.append(p, n)

    gtk.main()


if __name__ == '__main__':
    _test()


