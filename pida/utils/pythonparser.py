# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005 Ali Afshar aafshar@gmail.com

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


from cgi import escape

class SourceCodeNode(object):

    def __init__(self, filename, linenumber, nodename, nodetype, additional):
        self.filename = filename
        self.linenumber = linenumber
        self.nodename = nodename
        self.nodetype = nodetype or 'None'
        self.additional = additional
        self.node_colour = self.get_node_colour()
        self.ctype_markup = self.get_ctype_markup()
        self.nodename_markup = self.get_nodename_markup()
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def get_recursive_children(self):
        for node in self.children:
            yield node, self
            for child, parent in node.get_recursive_children():
                yield child, parent

    def get_node_colour(self):
        if self.nodetype == 'Class':
            return '#c00000'
        else:
            return '#0000c0'

    def get_ctype_markup(self):
        return '<span foreground="%s"><b><i>%s</i></b></span>' % (
            self.node_colour, self.nodetype[0])

    def get_nodename_markup(self):
        return '<tt><b>%s</b>\n%s</tt>' %  tuple(
            [escape(i) for i in  [self.nodename, self.additional]]
        )


try:
    from bike.parsing import fastparser
except ImportError:
    fastparser = None

def is_bike_installed():
    return fastparser is not None

def adapt_brm_node(node):
    firstline = node.getLine(0).strip()
    argnames = firstline.split(' ', 1)[-1].replace(node.name, '', 1)
    pida_node = SourceCodeNode(node.filename,
                                 node.linenum,
                                 node.name,
                                 node.type,
                                 argnames)
    return pida_node


def adapt_tree(roots, built=None):
    if built is None:
        built = SourceCodeNode('', 0, '', 'N', '')
    for root in roots:
        pnode = adapt_brm_node(root)
        built.add_child(pnode)
        adapt_tree(root.getChildNodes(), pnode)
    return built


def parse(stringdata):
    return fastparser.fastparser(stringdata).getChildNodes()


def get_nodes_from_string(stringdata):
    return adapt_tree(parse(stringdata))


