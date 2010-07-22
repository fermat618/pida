#! /usr/bin/env python

import sys

import os

from optparse import OptionParser

from pida.utils.puilder.execute import execute

def main():

    op = OptionParser()
    op.add_option('-t', '--target', dest='target')
    op.add_option('-d', '--directory', dest='directory')
    op.add_option('-s', '--script', dest='script')

    opts, args = op.parse_args(sys.argv)

    execute(
        project_directory=opts.directory,
        target_name=opts.target,
        project_file=opts.script,
    )


if __name__ == '__main__':
    sys.exit(main())

