#! /usr/bin/env python

import optparse, sys

import lplib as launchpadlib



def get_opts():
    usage = """
Console\t%prog -n [-r ROOT_URL] -p PRODUCT -t TITLE -c COMMENT
GUI\t%prog [-r ROOT_URL] [-p PRODUCT] [-t TITLE] [-c COMMENT]
Details\t%prog --help"""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-r', '--root-url', dest='root_url',
        action='store', type='string',
        help="""The base Launchpad URL. If not given defaults to
the main launchpad at %s.""" % launchpadlib.ROOT_URL)
    parser.add_option('-p', '--product-name', dest='product',
        action='store', type='string',
        help="""The product name to report. This option is compulsory for
console reports, where it will be the actual value.
For GUI reports, it is the prefilled name and can be
changed by the user""")
    parser.add_option('-t', '--title', dest='title',
        action='store', type='string',
        help="""The bug report title. This option is compulsory for
console reports, where it will be the actual value.
For GUI reports, it is the prefilled name and can be
changed by the user""")
    parser.add_option('-c', '--comment', dest='comment',
        action='store', type='string',
        help="""The bug report comment. This option is compulsory for
console reports, where it will be the actual value.
For GUI reports, it is the prefilled name and can be
changed by the user""")
    parser.add_option('-s', '--stdin-comment', dest='stdin_comment',
        action='store_true',
        help = """Read the comment text from stdin (overrides -c)""")
    parser.add_option('-n', '--no-gui', dest='no_gui',
        action='store_true',
        help="""Run in console (non-GUI mode)""")
    parser.add_option('-S', '--show-product', dest='show_product',
        action='store_true',
        help="""Show the product option (GUI only). The default behaviour
without this option is to show the product field if it has
not been priveded on the command line.""")
    opts, args = parser.parse_args()
    opts.product = opts.product or ''
    opts.title = opts.title or ''
    opts.comment = opts.comment or ''
    opts.root_url = opts.root_url or launchpadlib.ROOT_URL
    if opts.stdin_comment:
        opts.comment = sys.stdin.read()
    if not opts.product:
        opts.show_product = True
    if opts.no_gui:
        def _error(msg):
            parser.error('Must provide a %s for console reports' % msg)
        if not opts.product:
            _error('product')
        if not opts.title:
            _error('title')
        if not opts.comment:
            _error('comment')
    return opts, args


if __name__ == '__main__':
    opts, args = get_opts()
    if opts.no_gui:
        launchpadlib.console_report(opts)
    else:
        import gtkgui
        gtkgui.gui_report(opts)
    sys.exit(0)
