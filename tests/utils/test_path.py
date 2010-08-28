import os.path
from unittest import TestCase
from pida.utils.path import get_line_from_file, get_relative_path

class TestPath(TestCase):

    def test_rel_path(self):
        get_relative_path
        self.assertEqual(get_relative_path('/a/b/c/d', '/a/b/c1/d1'),
                         None)
        self.assertEqual(get_relative_path('/a/b/c/d', '/a/b/c/d/e/f'),
                         ['e', 'f'])
        self.assertEqual(get_relative_path('/a/b/c/d', '/a/b/c/d1'),
                         None)
        self.assertEqual(get_relative_path('/a/b/c/d', '/f/b/c/d'),
                         None)
        self.assertEqual(get_relative_path('/a/b', '/a/b/c/d'),
                         ['c', 'd'])
        self.assertEqual(get_relative_path('/a/b/c/d', '/a/'),
                         None)

    def test_get_line(self):
        fname = os.path.join(os.path.dirname(__file__), 'data', 'pathdata')
        self.assertEqual(get_line_from_file(fname, line=1),
                         'line 1')
        self.assertEqual(get_line_from_file(fname, line=3),
                         'line 3')
        self.assertEqual(get_line_from_file(fname, line=4),
                         '')
        self.assertEqual(get_line_from_file(fname, line=7),
                         'line 7 with more data so that it should return a very'
                         ' long string because it does not cap the length of'
                         ' the line returned and it in up to the caller to'
                         ' do so')
        self.assertEqual(get_line_from_file(fname, line=11),
                         'eof line 11 no linebreak')
        self.assertEqual(get_line_from_file(fname, offset=10),
                         'e 2')
        self.assertEqual(get_line_from_file(fname, offset=150),
                         'it in up to the caller to do so')
