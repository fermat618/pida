#!/usr/bin/python
# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A tool to generate the handbook.

Yes, generating the handbook is just a matter of typing

asciidoc -a icons -a quirks -a toc -a numbered -a toclevels=4 docs/txt/handbook.txt

in a console. But inserting the handbook in the website structure is a bit more
complex. Nothing that some DOM manipulation can manage though.
"""

# KNOWN BUGS:
#  . This script transforms '<' or '>' symbols in header stylesheets of
#      the online version. I suspect this is bad, but I guess header is
#      not used for the online version.
#

import getopt
import logging
import os.path
import subprocess
import sys


NOTICE = """Handbook generation for PIDA (http://pida.co.uk/)
This tool comes with ABSOLUTELY NO WARRANTY; for details use `-w'.
This is free software, and you are welcome to redistribute it under
certain conditions; see the COPYING file.
"""

WARRANTY = """  NO WARRANTY

  11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
mERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.

  12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.
"""

STYLESHEET_TOC = """
div#toctitle {
  color: #527bbd;
  font-family: sans-serif;
  font-size: 1.1em;
  font-weight: bold;
  margin-top: 1.0em;
  margin-bottom: 0.1em;
}

div.toclevel1, div.toclevel2, div.toclevel3, div.toclevel4 {
  margin-top: 0;
  margin-bottom: 0;
}
div.toclevel2 {
  margin-left: 2em;
  font-size: 0.9em;
}
div.toclevel3 {
  margin-left: 4em;
  font-size: 0.9em;
}
div.toclevel4 {
  margin-left: 6em;
  font-size: 0.9em;
}
"""

# Command line options
OPT_HELP = 'help'
OPT_OUTPUT = 'output'
OPT_QUIET = 'quiet'
OPT_SITE = 'site'
OPT_VERBOSE = 'verbose'
OPT_WARRANTY = 'warranty'

OPT_STOP = 'stop'


def print_notice():
    print NOTICE
    

def print_usage():
    print 'Usage: generate-handbook.py [-o|--output target] [-q] [-v] [-s|--site] source'
    print '       generate-handbook.py [-h|--help] [-w|--warranty]'


def print_gpl_warranty():
    print WARRANTY


def read_command_line(): 
    """Analyse command line.
    """
    options = []
    source = ''
    target = ''
    
    try:
        OPT_LIST = 'ho:qsvw'
        LONG_OPT_LIST = [OPT_HELP,
                         OPT_OUTPUT,
                         OPT_QUIET,
                         OPT_SITE,
                         OPT_VERBOSE,
                         OPT_WARRANTY]
        opt_list, args = getopt.getopt(sys.argv[1:], OPT_LIST, LONG_OPT_LIST)

    except getopt.GetoptError, e:
        print_usage()
        options.append(OPT_STOP)
        return '', '', options
    
    # In depth analyse
    for opt_name, opt_arg in opt_list:
        if opt_name in ('-h', '--' + OPT_HELP):
            print_usage()
            options.append(OPT_STOP)
            break
           
        elif opt_name in ('-o', '--' + OPT_OUTPUT):
            if opt_arg != '':
                target = opt_arg
            else:
                print '-o or --output needs an argument.'
                print_usage()
                options.append(OPT_STOP)

        elif opt_name in ('-q', '--' + OPT_QUIET):
            options.append(OPT_QUIET)
            if OPT_VERBOSE in options:
                print 'Quiet option conflicts with verbose.'
                options.append(OPT_STOP)

        elif opt_name in ('-s', '--' + OPT_SITE):
            options.append(OPT_SITE)

        elif opt_name in ('-v', '--' + OPT_VERBOSE):
            options.append(OPT_VERBOSE)
            if OPT_QUIET in options:
                print 'Verbose option conflicts with quiet.'
                options.append(OPT_STOP)                

        elif opt_name in ('-w', '--' + OPT_WARRANTY):
            print_gpl_warranty()
            options.append(OPT_STOP)
            break
        
    # Getting the filename to work on
    if not OPT_STOP in options:
        if len(args) == 0:
            print 'No source file.'
            print_usage()
            options.append(OPT_STOP)
        elif len(args) > 1:
            print 'Too many arguments.'
            print_usage()
            options.append(OPT_STOP)
        else:
            source = args[0]

        if target == '':
            split_name = os.path.splitext(source)
            target = split_name[0] + '.html'

    return source, target, options


def start_logging(verbosity):
    """Configure the logger.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s %(name)-25s:%(lineno) 4d\t%(levelname)s\t%(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger('handbook')
    logger.addHandler(handler)
    logger.setLevel(verbosity)


def do_asciidoc(source, target):
    """Invoke asciidoc.
    """
    logging.getLogger('handbook').info('generating xhtml output for %s', source)

    # Could have used directly asciidoc python structures if ascidoc wasn't
    # a long and monolithic script.
    args = ['-a', 'icons',
            '-a', 'quirks',
            '-a', 'toc',
            '-a', 'numbered',
            '-a', 'toclevels=4',
            '-o', target,
            source]
    return subprocess.call(['asciidoc'] + args)


def do_transform(source, target):
    """Do necessary transformations to put the asciidoc output in PIDA site.
    """
    logging.getLogger('handbook').info('transforming %s', source)
    try:
        import xml.dom.minidom
    except ImportError:
        logging.getLogger('handbook').error('couldn\'t import xml.dom.minidom!')
        return 1

    document = xml.dom.minidom.parse(source)

    body_elements = document.getElementsByTagName('body')
    if len(body_elements) != 1:
        logging.getLogger('handbook').error('invalid document: many bodies')
        return 1
    body_element = body_elements[0]
    
    # Change the id=\"header\" to class=\"header\".
    # Also remove the footer.
    div_elements = body_element.getElementsByTagName('div')
    for element in div_elements:
        if element.getAttribute(u'id') == u'header':
            logging.getLogger('handbook').debug('changing id into class')
            element.removeAttribute(u'id')
            element.setAttribute(u'class', u'header')
        elif element.getAttribute(u'id') == u'footer':
            logging.getLogger('handbook').debug('removing footer')
            element.parentNode.removeChild(element)
            #element.unlink()
            
    # Move the TOC script inside the body
    script_elements = document.getElementsByTagName('script')
    if len(script_elements) == 1:
        script_element = script_elements[0]
        parent_element = script_element.parentNode
        if parent_element:
            logging.getLogger('handbook').debug('moving the TOC script')
            parent_element.removeChild(script_element)
            body_element.appendChild(script_element)

            # Also fix the script so that it does only count handbook titles.
            logging.getLogger('handbook').debug('patching the TOC script')

            # Note that the first script element children are:
            #   - a text node ("/*")
            #   - a CDATA node ("window ...")
            # The string we must modify is in this second node, not in the
            # first text node.
            element = script_element.childNodes[1]
            element.data = element.data.replace(
                'var entries = tocEntries(document.getElementsByTagName("body")[0], toclevels);',
                'var entries = tocEntries(document.getElementById("doc"), toclevels);')
        else:
            logging.getLogger('handbook').error('no parent for script node')    
    else:
        logging.getLogger('handbook').warn('too many scripts to move the TOC one')

    # Copy the toc stylesheet inside the body
    logging.getLogger('handbook').debug('copying the TOC stylesheet')
    style_element = document.createElement('style')
    style_element.appendChild(document.createTextNode(STYLESHEET_TOC))
    body_element.insertBefore(style_element, body_element.firstChild)

    # XML writer tranforms empty anchors in the form <a />. This
    # leads to some rendering problems. Fix this by inserting a
    # space character in the anchors.
    logging.getLogger('handbook').debug('Fixing anchors bug')
    a_elements = document.getElementsByTagName('a')
    for element in a_elements:
        if element.hasAttribute(u'id') and element.childNodes == []:
            element.appendChild(document.createTextNode(' '))
    
    # Save the document
    string_doc = document.toxml(encoding='utf-8')
    try:
        f = open(target, 'w')
        f.write(string_doc)
    finally:
        f.close()
    document.unlink()

    return 0

    
# Main
source, target, options = read_command_line()
if OPT_STOP in options:
    sys.exit(2)
   
verbosity = logging.INFO
if OPT_QUIET in options:
    verbosity = logging.ERROR
elif OPT_VERBOSE in options:
    verbosity = logging.DEBUG
start_logging(verbosity)

if not OPT_QUIET in options:
    print_notice()

try:

    logging.getLogger('handbook').info('generate-handbook.py starting')

    if do_asciidoc(source, target) != 0:
        logging.getLogger('handbook').error('asciidoc failed')
        sys.exit(1)
    
    if OPT_SITE in options:
        split_name = os.path.splitext(target)
        split_name[0] + '-online.html'
        if do_transform(target, split_name[0] + '-site.html') != 0:
            logging.getLogger('handbook').error('transformation failed')
            sys.exit(1)

except SystemExit, e:
    pass
except KeyboardInterrupt, e:
    logging.getLogger('handbook').warn('Interrupted')
except Exception, e:
    logging.getLogger('handbook').error('Exception: %s', e)
    
