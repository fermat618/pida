# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005-2006 The PIDA Project

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
import logging
import logging.handlers

def build_logger(name, filepath):
    format_str = ('%(asctime)s '
                  '%(levelname)s '
                  '%(module)s.%(name)s:%(lineno)s '
                  '%(message)s')
    format = logging.Formatter(format_str)
    # logger
    logger = logging.getLogger(name)
    # to file
    handler = logging.handlers.RotatingFileHandler(filepath,
                                                   'a', 16000, 3)
    handler.setFormatter(format)
    logger.addHandler(handler)
    # optionally to stdout
    if 'PIDA_LOG_STDERR' in os.environ:
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        logger.addHandler(handler)
    if 'PIDA_DEBUG' in os.environ:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)
    return logger
