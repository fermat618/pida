#!/usr/bin/env python
from optparse import OptionParser
import sys, os, re
from datetime import date

import logging as log
log.basicConfig(level=log.INFO)

#log = logging.getLogger()

try:
    import jinja2
except ImportError, e:
    log.fatal("jinja2 is required for the creator script")
    sys.exit(1)


VALUES = {}
TYPE = "plugin"
path = ''

def is_bool(value):
    if value in ['y', 'Y']:
        return True
    if value in ['n', 'N']:
        return False
    return None

def generate():
    top = os.path.join(os.path.dirname(__file__), 'skeleton')
    for (dirpath, dirs, files) in os.walk(top):
        outdir = os.path.join(VALUES['path'], dirpath[len(top)+1:])
        for fname in files:
            if fname[-1] == '~' or fname[0] == '.':
                continue
            outname = fname.replace("skeleton", VALUES['name'])
            log.info("generate %s" %outname)
            tmpl = open(os.path.join(dirpath, fname)).read()
            jtemp = jinja2.Template(tmpl)
            content = jtemp.render(VALUES)
            fp = open(os.path.join(outdir, outname), 
                      "w")
            fp.write(content)
            fp.close()

        for dir in dirs:
            os.mkdir(os.path.join(outdir, dir))


def fill_details():
    global VALUES
    if TYPE == "service":
        defpath = os.path.join(os.getcwd(), 'pida', 'services')
    else:
        defpath = os.path.join(os.getcwd(), 'pida-plugins')
    path = raw_input('Please enter the path for the service [%s]: ' % defpath)
    if not path:
        path = defpath
    name = ''
    while not name:
        name = raw_input('Please enter the %s name [a-z_]+: ' %TYPE)
        if not re.match(r'[a-z_]+', name):
            name = None
    VALUES['path'] = os.path.join(path, name)
    VALUES['name'] = name
    VALUES['classname'] = name.capitalize()
    is_language = None
    while is_language is None:
        is_language = is_bool(raw_input('Is it a language plugin ? [y|N]: '))
        if is_language is None:
            is_language = False 

    VALUES['languageservice'] = is_language
    if is_language:
        language_names = None
        while not language_names:
            language_names = raw_input('Languages this plugin supports, seperated by ",": ')
        
        language_names = language_names.split(',')
        VALUES['language_names'] = language_names
    
        
    if os.path.exists(VALUES['path']):
        log.fatal("target directory exists: %s" %VALUES['path'])
        sys.exit(1)
    
    os.mkdir(VALUES['path'])
    generate()
    


def prime_parser():
    usage = "usage: %prog [options] [plugin|p|service|s]"
    parser = OptionParser(usage=usage)
    #parser.add_option('-n', '--no-svn',
    #    help='Do not add the creation to the subversion repo',
    #    dest='add_svn',
    #    action='store_false',
    #    default=True)
    return parser

def main():
    global TYPE
    parser = prime_parser()
    opts, args = parser.parse_args()
    act = len(args) and args[0] or None
    if act in ['service', 's']:
        TYPE = "service"
    elif act in ['plugin', 'p']:
        TYPE = "plugin"
    else:
        parser.error('You must provide an action')

    fill_details()


if __name__ == '__main__':
    main()
