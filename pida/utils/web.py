# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import base64

from urllib import urlencode
from urllib2 import urlopen, Request

from pida.utils.gthreads import AsyncTask

def fetch_url(url, content_callback, data={}, auth=None):
    """
    Asynchronously fetch a URL.

    It takes these arguments:

        ``url``: the url to fetch

        ``content_callback``: A function that is called with the URL's content

        ``data`` (optional): Additional POST data

        ``auth`` (optional): A tuple in the format (username, password) that's
                             used for http authentication

    """
    req = Request(url)

    if auth:
        base64string = base64.encodestring('%s:%s' % auth)[:-1]
        req.add_header("Authorization", "Basic %s" % base64string)

    if data:
        urlargs = (req, urlencode(data))
    else:
        urlargs = (req,)

    def _fetcher():
        try:
            f = urlopen(*urlargs)
            content = f.read()
            url = f.url
        except Exception, e:
            content = str(e)
            url = None
        return url, content

    task = AsyncTask(_fetcher, content_callback)
    task.start()

if __name__ == '__main__':
    def cc(url, data):
        print url, data
        gtk.main_quit()

    fetch_url('http://google.com/sdfsdfsdf', cc)
    import gtk
    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()

