# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import urllib, urllib2, cookielib, os, getpass


ROOT_URL = 'https://launchpad.net/'


def fake_opts(root_url=ROOT_URL,
              product='', show_product=False, title='', no_gui=False,
              comment=''):
    class Opts:
        pass
    o = Opts()
    o.root_url = root_url
    o.product = product
    o.show_product = show_product
    o.title = title
    o.no_gui = no_gui
    o.comment = comment
    return o, []



class LaunchpadClient(object):

    def __init__(self, launchpad_base_url):
        self._base_url = launchpad_base_url
        self._cookies = cookielib.CookieJar()
        req = urllib2.Request(self._base_url)
        resp = urllib2.urlopen(req)
        self._cookies.extract_cookies(resp, req)
    
    def login(self, username, password):
        data = {'form': 'login',
                'loginpage_email': username,
                'loginpage_password': password,
                'loginpage_submit_login': 'Log In'}
        url = self._base_url + 'products/+login'
        self._fetch(url, data)
    
    def submit_report(self, productpath, title, comment):
        data = {
            'field.title': title,
            'field.comment': comment,
            'field.private': '',
            'field.security_related': '',
            'field.security_related.used': '',
            'FORM_SUBMIT': 'Submit Bug Report',
        }
        url = self._base_url + productpath + '/+filebug'
        return self._fetch(url, data)
        
    def _fetch(self, url, data):
        postdata = urllib.urlencode(data)
        req = urllib2.Request(url, postdata)
        c = self._cookies._cookies_for_request(req)[0]
        req.add_header('Cookie', '%s=%s' % (c.name, c.value))
        return urllib2.urlopen(req).read()



def report_html(root_url, email, password, productpath, title, comment):
    client = LaunchpadClient(root_url)
    login_result = client.login(email, password)
    submit_result = client.submit_report(productpath, title, comment)
    return login_result, submit_result

from xmlrpclib import ServerProxy

def report(root_url, email, password, productpath, title, comment):
    s = ServerProxy('https://%s:%s@xmlrpc.launchpad.net/bugs/' %
        (email, password))
    d = dict(
        product=productpath,
        summary=title,
        comment=comment,
    )
    try:
        return True, s.filebug(d)
    except Exception, e:
        return False, str(e)



def get_local_config():
    configfile = os.path.expanduser('~/.launchpad-client')
    try:
        f = open(configfile)
        name = f.readline().strip()
        password = f.readline().strip()
        return (name, password)
    except (OSError, IOError):
        return (None, None)

def save_local_config(email, password):
    configfile = os.path.expanduser('~/.launchpad-client')
    f = open(configfile, 'w')
    f.write('%s\n%s\n\n' % (email, password))
    f.close()


def console_report(opts):
    email, password = get_local_config()
    if not email:
        email = raw_input('Email address: ')
    if not password:
        password = getpass.getpass('Password: ')
    product = 'products/%s/' % opts.product
    report(opts.root_url, email, password, product, opts.title, opts.comment)






