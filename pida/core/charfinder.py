# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    Chartype detection

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import codecs
import re

# list of mimetypes that are known to be text
# will be filled by languge service
text_mime = set()

dumb_encodings = ["utf-8", "iso-8859-15", "windows-1252"]

def dumb_detect(stream, filename, mimetype):
    for encoding in dumb_encodings:
        try:
            codecs.open(filename, encoding=encoding).read()
            return encoding
        except UnicodeDecodeError:
            pass

PY_ENC = re.compile(r"coding: ([\w\-_0-9]+)")
def python_detect(stream, filename, mimetype):
    def find_one():
        match = PY_ENC.search(stream.readline())
        if match:
            return match.group(1)

    return find_one() or find_one()

try:
    from pida.utils import magic

    WELL_KNOWN = ['ISO-8859', 'ASCII', 'UTF-8', 'UTF-16LE', 'UTF-16BE',
                  'UTF-32BE', 'UTF-32LE']
    FAILED = []

    def _magic_enc(type_):
        if type_ in WELL_KNOWN:
            return type_
        if type_ in FAILED:
            return None
        try:
            #why does codecs don't have a list of this ????
            codecs.lookup(type_)
            return type_
        except LookupError:
            FAILED.append(type_)
            return None


    def magic_detect(stream, filename, mimetype):
        if filename:
            mime = magic.Magic(mime=True).from_file(filename)
            if mime[:5] == 'text/':
                # magic return often a to specific content that does not
                # contain the encoding :-(
                return _magic_enc(magic.Magic().from_file(filename).split()[0])
        elif stream:
            # very bad
            chunk = stream.read()
            mime = magic.Magic(mime=True).from_buffer(chunk)
            if mime[:5] == 'text/':
                return _magic_enc(magic.Magic().from_buffer(chunk).split()[0])


    def magic_test(stream, filename, mimetype):
        if filename:
            mime = magic.Magic(mime=True).from_file(filename)
            if mime[:5] == 'text/':
                return True
            elif mime in text_mime:
                return True
            return False
        elif stream:
            # very bad
            chunk = stream.read()
            mime = magic.Magic(mime=True).from_buffer(chunk)
            if mime[:5] == 'text/':
                return True
            elif mime in text_mime:
                return True
            return False


except AttributeError, e:
    print "can't load magic module"
    magic_detect = lambda * k: None
    magic_test = lambda * k: None


try:
    from chardet.universaldetector import UniversalDetector

    def chardet_sniff(stream, filename, mimetype):
        detector = UniversalDetector()
        chunk = stream.read(4086)
        while chunk and not detector.done:
            detector.feed(chunk)
            chunk = stream.read(4086)

        detector.close()
        return detector.result["encoding"]

except ImportError:
    chardet_sniff = lambda * k: None

mime_detectors = {
    ('text', 'x-python'): python_detect,
}

def detect_mime(stream, filename, mimetype):
    if mimetype in mime_detectors:
        return mime_detectors[mimetype](stream, filename, mimetype)

detectors = [detect_mime, magic_detect, chardet_sniff, dumb_detect]
text_detectors = [magic_test]

def detect_encoding(stream, filename, mimetype):
    """
    Detect and returns the encoding of:

    @stream: fileobject
    @filename: absolute path
    @mimetype: mimetype
    """
    for encoder in detectors:
        encoding = encoder(stream, filename, mimetype)
        stream.seek(0)
        if encoding is not None:
            return encoding

    return 'ASCII' #XXX this seems a bit insane

def detect_text(stream, filename, mimetype):
    """
    Detects if the input is of type text and returns True

    @stream: fileobject
    @filename: absolute path
    @mimetype: mimetype
    """
    if mimetype:
        if mimetype[:5] == 'text/':
            return True
        if mimetype in text_mime:
            return True

    for encoder in text_detectors:
        rv = encoder(stream, filename, mimetype)
        if rv is not None:
            return rv

    #try the rest..
    # chardetsniff wont work, it finds libraries as text..
    for encoder in [dumb_detect]:
        encoding = encoder(stream, filename, mimetype)
        stream.seek(0)
        if encoding is not None:
            print encoder, encoding
            return True

    return False
