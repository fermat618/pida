# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

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

import os


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
    else:
        return None

           


if __name__ == '__main__':
    print get_relative_path('/a/b/c/d', '/a/b/c1/d1')
    print get_relative_path('/a/b/c/d', '/a/b/c/d/e/f')
    print get_relative_path('/a/b/c/d', '/a/b/c/d1')
    print get_relative_path('/a/b/c/d', '/a/b/c')




# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
