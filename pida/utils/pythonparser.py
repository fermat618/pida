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


# bike.transformer.save

outputqueue = {}

def resetOutputQueue():
    global outputqueue
    outputqueue = {}

# bike.parsing.parserutils

#from __future__ import generators
import re

escapedQuotesRE = re.compile(r"(\\\\|\\\"|\\\')")

# changess \" \' and \\ into ** so that text searches
# for " and ' won't hit escaped ones
def maskEscapedQuotes(src):
    return escapedQuotesRE.sub("**", src)

stringsAndCommentsRE =  \
      re.compile("(\"\"\".*?\"\"\"|'''.*?'''|\"[^\"]*\"|\'[^\']*\'|#.*?\n)", re.DOTALL)

import string
#transtable = string.maketrans('classdefifforwhiletry', "*********************")

# performs a transformation on all of the comments and strings so that
# text searches for python keywords won't accidently find a keyword in
# a string or comment
def maskPythonKeywordsInStringsAndComments(src):
    src = escapedQuotesRE.sub("**", src)
    allstrings = stringsAndCommentsRE.split(src)
    # every odd element is a string or comment
    for i in xrange(1, len(allstrings), 2):
        allstrings[i] = allstrings[i].upper()
        #allstrings[i] = allstrings[i].translate(transtable)
    return "".join(allstrings)


allchars = string.maketrans("", "")
allcharsExceptNewline = allchars[: allchars.index('\n')]+allchars[allchars.index('\n')+1:]
allcharsExceptNewlineTranstable = string.maketrans(allcharsExceptNewline, '*'*len(allcharsExceptNewline))


# replaces all chars in a string or a comment with * (except newlines).
# this ensures that text searches don't mistake comments for keywords, and that all
# matches are in the same line/comment as the original
def maskStringsAndComments(src):
    src = escapedQuotesRE.sub("**", src)
    allstrings = stringsAndCommentsRE.split(src)
    # every odd element is a string or comment
    for i in xrange(1, len(allstrings), 2):
        if allstrings[i].startswith("'''")or allstrings[i].startswith('"""'):
            allstrings[i] = allstrings[i][:3]+ \
                           allstrings[i][3:-3].translate(allcharsExceptNewlineTranstable)+ \
                           allstrings[i][-3:]
        else:
            allstrings[i] = allstrings[i][0]+ \
                           allstrings[i][1:-1].translate(allcharsExceptNewlineTranstable)+ \
                           allstrings[i][-1]

    return "".join(allstrings)


# replaces all chars in a string or a comment with * (except newlines).
# this ensures that text searches don't mistake comments for keywords, and that all
# matches are in the same line/comment as the original
def maskStringsAndRemoveComments(src):
    src = escapedQuotesRE.sub("**", src)
    allstrings = stringsAndCommentsRE.split(src)
    # every odd element is a string or comment
    for i in xrange(1, len(allstrings), 2):
        if allstrings[i].startswith("'''")or allstrings[i].startswith('"""'):
            allstrings[i] = allstrings[i][:3]+ \
                           allstrings[i][3:-3].translate(allcharsExceptNewlineTranstable)+ \
                           allstrings[i][-3:]
        elif allstrings[i].startswith("#"):
            allstrings[i] = '\n'
        else:
            allstrings[i] = allstrings[i][0]+ \
                           allstrings[i][1:-1].translate(allcharsExceptNewlineTranstable)+ \
                           allstrings[i][-1]
    return "".join(allstrings)
        

implicitContinuationChars = (('(', ')'), ('[', ']'), ('{', '}'))
emptyHangingBraces = [0,0,0,0,0]
linecontinueRE = re.compile(r"\\\s*(#.*)?$")
multiLineStringsRE =  \
      re.compile("(^.*?\"\"\".*?\"\"\".*?$|^.*?'''.*?'''.*?$)", re.DOTALL)

#def splitLogicalLines(src):
#    src = multiLineStringsRE.split(src)

# splits the string into logical lines.  This requires the comments to
# be removed, and strings masked (see other fns in this module)
def splitLogicalLines(src):
    physicallines = src.splitlines(1)
    return [x for x in generateLogicalLines(physicallines)]


class UnbalancedBracesException: pass

# splits the string into logical lines.  This requires the strings
# masked (see other fns in this module)
# Physical Lines *Must* start on a non-continued non-in-a-comment line
# (although detects unbalanced braces)
def generateLogicalLines(physicallines):
    tmp = []
    hangingBraces = list(emptyHangingBraces)
    hangingComments = 0
    for line in physicallines:
        # update hanging braces
        for i in range(len(implicitContinuationChars)):
            contchar = implicitContinuationChars[i]
            numHanging = hangingBraces[i]
            hangingBraces[i] = numHanging+line.count(contchar[0]) - \
                               line.count(contchar[1])

        hangingComments ^= line.count('"""') % 2
        hangingComments ^= line.count("'''") % 2

        if hangingBraces[0] < 0 or \
           hangingBraces[1] < 0 or \
           hangingBraces[2] < 0:
            raise UnbalancedBracesException()
        
        if linecontinueRE.search(line):
            tmp.append(line)
        elif hangingBraces != emptyHangingBraces:
            tmp.append(line)
        elif hangingComments:
            tmp.append(line)
        else:
            tmp.append(line)
            yield "".join(tmp)
            tmp = []
    

# see above but yields (line,linenum)
#   needs physicallines to have linenum attribute
#   TODO: refactor with previous function
def generateLogicalLinesAndLineNumbers(physicallines):
    tmp = []
    hangingBraces = list(emptyHangingBraces)
    hangingComments = 0
    linenum = None
    for line in physicallines:
        if tmp == []:
            linenum = line.linenum

        # update hanging braces
        for i in range(len(implicitContinuationChars)):
            contchar = implicitContinuationChars[i]
            numHanging = hangingBraces[i]
            hangingBraces[i] = numHanging+line.count(contchar[0]) - \
                               line.count(contchar[1])

        hangingComments ^= line.count('"""') % 2
        hangingComments ^= line.count("'''") % 2
            
        if linecontinueRE.search(line):
            tmp.append(line)
        elif hangingBraces != emptyHangingBraces:
            tmp.append(line)
        elif hangingComments:
            tmp.append(line)
        else:
            tmp.append(line)
            yield "".join(tmp),linenum
            tmp = []
        



# takes a line of code, and decorates it with noops so that it can be
# parsed by the python compiler.
# e.g.  "if foo:"  -> "if foo: pass"
# returns the line, and the adjustment made to the column pos of the first char
# line must have strings and comments masked
#
# N.B. it only inserts keywords whitespace and 0's
notSpaceRE = re.compile("\s*(\S)")
commentRE = re.compile("#.*$")

def makeLineParseable(line):
    return makeLineParseableWhenCommentsRemoved(commentRE.sub("",line))

def makeLineParseableWhenCommentsRemoved(line):
    line = line.strip()
    if ":" in line:
        if line.endswith(":"):
            line += " pass"
        if line.startswith("try"):
            line += "\nexcept: pass"
        elif line.startswith("except") or line.startswith("finally"):
            line = "try: pass\n" + line
            return line
        elif line.startswith("else") or line.startswith("elif"):
            line = "if 0: pass\n" + line
            return line
    elif line.startswith("yield"):
        return ("return"+line[5:])
    return line

# bike.parsing.parserast

#from __future__ import generators
#from parserutils import generateLogicalLines, maskStringsAndComments, maskStringsAndRemoveComments
import re
import os
import compiler
#from bike.transformer.save import resetOutputQueue

TABWIDTH = 4

classNameRE = re.compile("^\s*class\s+(\w+)")
fnNameRE = re.compile("^\s*def\s+(\w+)")

_root = None

def getRoot():
    global _root
    if _root is None:
        resetRoot()
    return _root 

def resetRoot(root = None):
    global _root
    _root = root or Root()
    _root.unittestmode = False
    resetOutputQueue()


def getModule(filename_path):
    from bike.parsing.load import CantLocateSourceNodeException, getSourceNode
    try:
        sourcenode = getSourceNode(filename_path)
        return sourcenode.fastparseroot
    except CantLocateSourceNodeException:
        return None

def getPackage(directory_path):
    from bike.parsing.pathutils import getRootDirectory
    rootdir = getRootDirectory(directory_path)
    if rootdir == directory_path:
        return getRoot()
    else:
        return Package(directory_path,
                       os.path.basename(directory_path))




            
class Root:
    def __init__(self, pythonpath = None):
        # singleton hack to allow functions in query package to appear
        # 'stateless'
        resetRoot(self)

        # this is to get round a python optimisation which reuses an
        # empty list as a default arg. unfortunately the client of
        # this method may fill that list, so it's not empty
        if not pythonpath:
            pythonpath = []
        self.pythonpath = pythonpath

    def __repr__(self):
        return "Root()"
        #return "Root(%s)"%(self.getChildNodes())


    # dummy method
    def getChild(self,name):
        return None

class Package:
    def __init__(self, path, name):
        self.path = path
        self.name = name

    def getChild(self,name):
        from bike.parsing.newstuff import getModule
        return getModule(os.path.join(self.path,name+".py"))

    def __repr__(self):
        return "Package(%s,%s)"%(self.path, self.name)

# used so that linenum can be an attribute
class Line(str):
    pass

class StructuralNode:
    def __init__(self, filename, srclines, modulesrc):
        self.childNodes = []
        self.filename = filename
        self._parent = None
        self._modulesrc = modulesrc
        self._srclines = srclines
        self._maskedLines = None

    def addChild(self, node):
        self.childNodes.append(node)
        node.setParent(self)

    def setParent(self, parent):
        self._parent = parent

    def getParent(self):
        return self._parent

    def getChildNodes(self):
        return self.childNodes

    def getChild(self,name):
        matches = [c for c in self.getChildNodes() if c.name == name]
        if matches != []:
            return matches[0]

    def getLogicalLine(self,physicalLineno):
        return generateLogicalLines(self._srclines[physicalLineno-1:]).next()

    # badly named: actually returns line numbers of import statements
    def getImportLineNumbers(self):
        try:
            return self.importlines
        except AttributeError:
            return[]

    def getLinesNotIncludingThoseBelongingToChildScopes(self):
        srclines = self.getMaskedModuleLines()
        lines = []
        lineno = self.getStartLine()
        for child in self.getChildNodes():
            lines+=srclines[lineno-1: child.getStartLine()-1]
            lineno = child.getEndLine()
        lines+=srclines[lineno-1: self.getEndLine()-1]
        return lines


    def generateLinesNotIncludingThoseBelongingToChildScopes(self):
        srclines = self.getMaskedModuleLines()
        lines = []
        lineno = self.getStartLine()
        for child in self.getChildNodes():
            for line in srclines[lineno-1: child.getStartLine()-1]:
                yield self.attachLinenum(line,lineno)
                lineno +=1
            lineno = child.getEndLine()
        for line in srclines[lineno-1: self.getEndLine()-1]:
            yield self.attachLinenum(line,lineno)
            lineno +=1

    def generateLinesWithLineNumbers(self,startline=1):
        srclines = self.getMaskedModuleLines()
        for lineno in range(startline,len(srclines)+1):
            yield self.attachLinenum(srclines[lineno-1],lineno)

    def attachLinenum(self,line,lineno):
        line = Line(line)
        line.linenum = lineno
        return line

    def getMaskedModuleLines(self):
        from bike.parsing.load import Cache
        try:
            maskedlines = Cache.instance.maskedlinescache[self.filename]
        except:
            # make sure src is actually masked
            # (could just have keywords masked)
            maskedsrc = maskStringsAndComments(self._modulesrc)
            maskedlines = maskedsrc.splitlines(1)
            Cache.instance.maskedlinescache[self.filename] = maskedlines
        return maskedlines


class Module(StructuralNode):
    def __init__(self, filename, name, srclines, maskedsrc):
        StructuralNode.__init__(self, filename, srclines, maskedsrc)
        self.name = name
        self.indent = -TABWIDTH
        self.flattenedNodes = []
        self.module = self

    def getMaskedLines(self):
        return self.getMaskedModuleLines()

    def getFlattenedListOfChildNodes(self):
        return self.flattenedNodes

    def getStartLine(self):
        return 1

    def getEndLine(self):
        return len(self.getMaskedModuleLines())+1

    def getSourceNode(self):
        return self.sourcenode

    def setSourceNode(self, sourcenode):
        self.sourcenode = sourcenode

    def matchesCompilerNode(self,node):
        return isinstance(node,compiler.ast.Module) and \
               node.name == self.name

    def getParent(self):
        if self._parent is not None:
            return self._parent
        else:
            from newstuff import getPackage
            return getPackage(os.path.dirname(self.filename))


    def __str__(self):
        return "bike:Module:"+self.filename

indentRE = re.compile("^(\s*)\S")
class Node:
    # module = the module node
    # linenum = starting line number
    def __init__(self, name, module, linenum, indent):
        self.name = name
        self.module = module
        self.linenum = linenum
        self.endline = None
        self.indent = indent

    def getMaskedLines(self):
        return self.getMaskedModuleLines()[self.getStartLine()-1:self.getEndLine()-1]

    def getStartLine(self):
        return self.linenum

    def getEndLine(self):
        if self.endline is None:
            physicallines = self.getMaskedModuleLines()
            lineno = self.linenum
            logicallines = generateLogicalLines(physicallines[lineno-1:])

            # skip the first line, because it's the declaration
            line = logicallines.next()
            lineno+=line.count("\n")

            # scan to the end of the fn
            for line in logicallines:
                #print lineno,":",line,
                match = indentRE.match(line)
                if match and match.end()-1 <= self.indent:
                    break
                lineno+=line.count("\n")
            self.endline = lineno
        return self.endline

    # linenum starts at 0
    def getLine(self, linenum):
        return self._srclines[(self.getStartLine()-1) + linenum]


baseClassesRE = re.compile("class\s+[^(]+\(([^)]+)\):")

class Class(StructuralNode, Node):
    def __init__(self, name, filename, module, linenum, indent, srclines, maskedmodulesrc):
        StructuralNode.__init__(self, filename, srclines, maskedmodulesrc)
        Node.__init__(self, name, module, linenum, indent)
        self.type = "Class"

    
    def getBaseClassNames(self):
        #line = self.getLine(0)
        line = self.getLogicalLine(self.getStartLine())
        match = baseClassesRE.search(line)
        if match:
            return [s.strip()for s in match.group(1).split(",")]
        else:
            return []

    def getColumnOfName(self):
        match = classNameRE.match(self.getLine(0))
        return match.start(1)

    def __repr__(self):
        return "<bike:Class:%s>" % self.name

    def __str__(self):
        return "bike:Class:"+self.filename+":"+\
               str(self.getStartLine())+":"+self.name

    def matchesCompilerNode(self,node):
        return isinstance(node,compiler.ast.Class) and \
               node.name == self.name

    def __eq__(self,other):
        return isinstance(other,Class) and \
               self.filename == other.filename and \
               self.getStartLine() == other.getStartLine()

# describes an instance of a class
class Instance:
    def __init__(self, type):
        assert type is not None
        self._type = type

    def getType(self):
        return self._type

    def __str__(self):
        return "Instance(%s)"%(self.getType())


class Function(StructuralNode, Node):
    def __init__(self, name, filename, module, linenum, indent,
                 srclines, maskedsrc):
        StructuralNode.__init__(self, filename, srclines, maskedsrc)
        Node.__init__(self, name, module, linenum, indent)
        self.type = "Function"

    def getColumnOfName(self):
        match = fnNameRE.match(self.getLine(0))
        return match.start(1)

    def __repr__(self):
        return "<bike:Function:%s>" % self.name

    def __str__(self):
        return "bike:Function:"+self.filename+":"+\
               str(self.getStartLine())+":"+self.name

    def matchesCompilerNode(self,node):
        return isinstance(node,compiler.ast.Function) and \
               node.name == self.name


# bike.parsing.fastparser

#!/usr/bin/env python
#from bike.parsing.fastparserast import *
#from bike.parsing.parserutils import *
from parser import ParserError
#import exceptions

indentRE = re.compile("^\s*(\w+)")

# returns a tree of objects representing nested classes and functions
# in the source
def fastparser(src,modulename="",filename=""):
    try:
        return fastparser_impl(src,modulename,filename)
    except RuntimeError, ex:   # if recursive call exceeds maximum depth
        if str(ex) == "maximum recursion limit exceeded":
            raise ParserError,"maximum recursion depth exceeded when fast-parsing src "+filename
        else:
            raise

def fastparser_impl(src,modulename,filename):
    lines = src.splitlines(1)
    maskedSrc = maskPythonKeywordsInStringsAndComments(src)
    maskedLines = maskedSrc.splitlines(1)
    root = Module(filename,modulename,lines,maskedSrc)
    parentnode = root
    lineno = 0
    for line in maskedLines:
        lineno+=1
        #print "line",lineno,":",line
        m = indentRE.match(line)
        if m:
            indent = m.start(1)
            tokenstr = m.group(1)
            if tokenstr == "import" or tokenstr == "from":
                while indent <= parentnode.indent:   # root indent is -TABWIDTH
                    parentnode = parentnode.getParent()
                try:
                    parentnode.importlines.append(lineno)
                except AttributeError:
                    parentnode.importlines = [lineno]
            elif tokenstr == "class":
                m2 = classNameRE.match(line)
                if m2:
                    n = Class(m2.group(1), filename, root, lineno, indent, lines, maskedSrc)
                    root.flattenedNodes.append(n)

                    while indent <= parentnode.indent:
                        parentnode = parentnode.getParent()
                    parentnode.addChild(n)
                    parentnode = n

            elif tokenstr == "def":
                m2 = fnNameRE.match(line)
                if m2:
                    n = Function(m2.group(1), filename, root, lineno, indent, lines, maskedSrc)
                    root.flattenedNodes.append(n)

                    while indent <= parentnode.indent:
                        parentnode = parentnode.getParent()
                    parentnode.addChild(n)
                    parentnode = n

            elif indent <= parentnode.indent and \
                     tokenstr in ['if','for','while','try']:
                parentnode = parentnode.getParent()
                while indent <= parentnode.indent:
                    parentnode = parentnode.getParent()

    return root


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


#from bike.parsing import fastparser


#def is_bike_installed():
#    return fastparser is not None


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
    return fastparser(stringdata).getChildNodes()


def get_nodes_from_string(stringdata):
    return adapt_tree(parse(stringdata))


