

import os

meta_tmpl = """[meta]
name =
title =
shortcut =

[variables]
"""

def get_location():
    location = raw_input('Directory to store the snippet: [~/.pida2/snippets/]: ')
    location = os.path.expanduser(location.strip())
    if not location:
        location = os.path.expanduser('~/.pida2/snippets/')
    return location

def get_name():
    name = raw_input('Enter snippet name: ')
    name = name.strip()
    if not name:
        raise Exception('You must enter a name')
    else:
        return name

def create_snippet(location, name):
    base = os.path.join(location, name)
    meta = base + '.meta'
    tmpl = base + '.tmpl'
    f = open(meta, 'w')
    f.write(meta_tmpl)
    f.close()
    open(tmpl, 'w').close()

def main():
    location = get_location()
    name = get_name()
    create_snippet(location, name)

if __name__ == '__main__':
    main()
