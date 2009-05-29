# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    Chartype detection

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import codecs
import re

dumb_encodings = ["utf-8", "iso-8859-15", "windows-1252"]

def dumb_detect(stream, filename, mimetype):
    for encoding in dumb_encodings:
        try:
            codecs.open(filename, encoding=encoding).read()
            return encoding
        except UnicodeDecodeError:
            pass
    return "ascii" #XXX this seems a bit insane

PY_ENC = re.compile(r"coding: ([\w\-_0-9]+)")
def python_detect(stream, filename, mimetype):
    def find_one():
        match = PY_ENC.search(stream.readline())
        if match:
            return match.group(1)

    return find_one() or find_one()


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
    chardet_sniff = lambda *k: None

mime_detectors = {
    ('text', 'x-python'): python_detect,
}

def detect_mime(stream, filename, mimetype):
    if mimetype in mime_detectors:
        return mime_detectors[mimetype](stream, filename, mimetype)

detectors = [detect_mime, chardet_sniff, dumb_detect]

def detect_encoding(stream, filename, mimetype):
    for encoder in detectors:
        encoding = encoder(stream, filename, mimetype)
        stream.seek(0)
        if encoding is not None:
            return encoding
