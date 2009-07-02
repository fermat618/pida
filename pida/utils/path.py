# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os

homedir = os.path.expanduser('~')

def get_relative_path(from_path, to_path):
    """Get the relative path to to_path from from_path"""
    from_list = from_path.split(os.sep)
    to_list = to_path.split(os.sep)
    final_list = list(to_list)
    common = []
    uncommon = []
    if len(to_list) > len(from_list):
        for i, segment in enumerate(from_list):
            if to_list[i] == segment:
                final_list.pop(0)
            else:
                return None
        return final_list
    elif to_list == from_list:
        # the relative path between the same paths is an empty sequence
        return []
    else:
        return None

def walktree(top = ".", depthfirst = True, skipped_directory = []):
    """Walk the directory tree, starting from top. Credit to Noah Spurrier and Doug Fort."""
    import os, stat
    names = os.listdir(top)
    if not depthfirst:
        yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            if name in skipped_directory:
                continue
            for (newtop, children) in walktree (os.path.join(top, name),
                    depthfirst, skipped_directory):
                yield newtop, children
    if depthfirst:
        names = [name for name in names if name not in skipped_directory]
        yield top, names

def get_line_from_file(file_name, line=None, offset=None):
    """
    Returns the line of a file. It removes trailing newlines and whitespaces.
    
    @line: linenumber 
    @offset: offset of file
    """ 
    if line is None and offset is None:
        raise ValueError('At least on of line or offset must be set')
    fp = open(file_name)
    if line is not None:
        i = 0
        for fline in fp:
            i += 1
            if i == line:
                return fline.strip()
    else:
        fp.seek(offset)
        return fp.readline().strip()
        
    return None

if __name__ == '__main__':
    print get_relative_path('/a/b/c/d', '/a/b/c1/d1')
    print get_relative_path('/a/b/c/d', '/a/b/c/d/e/f')
    print get_relative_path('/a/b/c/d', '/a/b/c/d1')
    print get_relative_path('/a/b/c/d', '/a/b/c')



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
