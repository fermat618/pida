#!/usr/bin/python

import urllib
import urllib2
import mimetools, mimetypes
import os
import StringIO
import logging
log = logging.getLogger('pida.http')
# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.get_data()
        if data is not None and not isinstance(data, str):
            files = []
            vars = []
            try:
                 for key, value in data.iteritems():
                     #XXX; better check
                     if hasattr(value, 'read'):
                         files.append((key, value))
                     else:
                         vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError, "not a valid non-string sequence or mapping object", traceback

            if not files:
                data = urllib.urlencode(vars, doseq)
            else:
                boundary = mimetools.choose_boundary()
                data = encode_multipart(vars, files, boundary)
                contenttype = 'multipart/form-data; boundary=%s' % boundary
                if (request.has_header('Content-Type')
                    and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    log.debug("replace Content-Type %s with %s %s" % (request.get_header('content-type'), 'multipart/form-data'))
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)
        return request



def encode_vars(vars, boundary):
    for key, value in vars:
        yield '--%s\r\n' % boundary
        yield 'Content-Disposition: form-data; name="%s"' % key
        yield '\r\n\r\n'
        yield value
        yield '\r\n'

def encode_file(key, fd, boundary):
    name = getattr(fd, 'name', 'unknown') #stringio :/
    name = os.path.basename(name)
    contenttype = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    yield '--%s\r\n' % boundary
    yield 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, name)
    yield 'Content-Type: %s\r\n' % contenttype
    yield '\r\n'
    fd.seek(0)
    yield fd.read()
    yield '\r\n'

def encode_multipart(vars, files, boundary):
    data = []
    data.extend(encode_vars(vars, boundary))
    for key, fd in files:
        data.extend(encode_file(key, fd, boundary))
    data.append('--%s--\r\n\r\n' % boundary)
    return ''.join(data)


if __name__=="__main__":
    import sys
    validator = "http://validator.w3.org/check"
    opener = urllib2.build_opener(MultipartPostHandler)

    def validate_file(url):
        io = StringIO.StringIO()
        io.write(opener.open(url).read())
        io.name = 'test.html' # look like a file
        params = { "ss" : "0",            # show source
                   "doctype" : "Inline",
                   "uploaded_file" : io }
        print opener.open(validator, params).read()

    if sys.argv[1:]:
        for arg in sys.argv[1:]:
            validate_file(arg)
    else:
        validate_file("http://www.google.com")

