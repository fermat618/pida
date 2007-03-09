__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import unittest
from text import *

class TestLineIterator(unittest.TestCase):
    def test_empty(self):
        buff = gtk.TextBuffer()
        buff.set_text("")
        bounds = buff.get_bounds()
        iters = list(line_iterator(buff, *bounds))
        self.assertEquals(1, len(iters))
        assert iters[0].equal(bounds[0])
        assert iters[0].equal(bounds[1])
    
    def test_one_line(self):
        buff = gtk.TextBuffer()
        buff.set_text("\n")
        bounds = buff.get_bounds()
        iters = list(line_iterator(buff, *bounds))
        self.assertEquals(2, len(iters))
        assert iters[0].equal(bounds[0])
        assert iters[1].equal(bounds[1])

    def test_many_lines(self):
        buff = gtk.TextBuffer()
        buff.set_text("a\nb\nbar")
        bounds = buff.get_bounds()
        iters = list(line_iterator(buff, *bounds))
        self.assertEquals(3, len(iters))
    
    def test_middle_line(self):
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        self.assertEquals("23\n\n", buff.get_text(start_iter, end_iter))
        iters = list(line_iterator(buff, start_iter, end_iter))

        self.assertEquals(3, len(iters))




class TestSelectedLineIterator(unittest.TestCase):
    def test_empty(self):
        buff = gtk.TextBuffer()
        buff.set_text("")
        iters = list(selected_line_iterator(buff))
        self.assertEquals(0, len(iters))

    def test_empty2(self):
        buff = gtk.TextBuffer()
        buff.set_text("foo\nbar\ngaz")
        iters = list(selected_line_iterator(buff))
        self.assertEquals(0, len(iters))

    def test_middle_line(self):
        # In this case we only select the '2'
        # The only iterator should be the begining of the first line
        buff = gtk.TextBuffer()
        buff.set_text("123\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(1)
        self.assertEquals("2", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("2", buff.get_text(*buff.get_selection_bounds()))
        iters = list(selected_line_iterator(buff))
        self.assertEquals(1, len(iters))
        
        assert iters[0].equal(buff.get_start_iter())

    def test_middle_line2(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("123\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        self.assertEquals("23\nb", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\nb", buff.get_text(*buff.get_selection_bounds()))
        iters = list(selected_line_iterator(buff))
        self.assertEquals(2, len(iters))
        
        assert iters[0].equal(buff.get_start_iter())
        assert iters[1].starts_line()

    def test_skip_line(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        self.assertEquals("23\n\n", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\n", buff.get_text(*buff.get_selection_bounds()))

        iters = list(selected_line_iterator(buff))

        self.assertEquals(1, len(iters))
        assert iters[0].equal(buff.get_start_iter())

    def test_skip_first_line(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        end_iter = start_iter.copy()
        end_iter.forward_chars(3)
        self.assertEquals("\n\nb", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("\n\nb", buff.get_text(*buff.get_selection_bounds()))
        iters = list(selected_line_iterator(buff))
        
        self.assertEquals(1, len(iters))

    def test_skip_middle_line(self):
        # In this case we select the '23' an empty line and a 'b'
        # The first iterator should be the begining of the first line
        # The second iterator should be the begining of the third line
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(5)
        self.assertEquals("23\n\nb", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\nb", buff.get_text(*buff.get_selection_bounds()))
        iters = list(selected_line_iterator(buff))
        self.assertEquals(2, len(iters))
        
        assert iters[0].equal(buff.get_start_iter())
        assert iters[1].starts_line()


    def test_full(self):
        # In this case we select the '23' an empty line and a 'b'
        # The first iterator should be the begining of the first line
        # The second iterator should be the begining of the third line
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter, end_iter = buff.get_bounds()
        self.assertEquals("123\n\nbar\ngaz", buff.get_text(start_iter, end_iter))
        buff.select_range(start_iter, end_iter)
        self.assertEquals("123\n\nbar\ngaz", buff.get_text(*buff.get_selection_bounds()))
        iters = list(selected_line_iterator(buff))
        self.assertEquals(3, len(iters))
        
        assert iters[0].equal(buff.get_start_iter())
        assert iters[1].starts_line()
        assert iters[2].starts_line()
    

class TestIndentSelected(unittest.TestCase):
    def checkSelected(self, buff, text):
        self.assertEquals(text, buff.get_text(*buff.get_bounds()))
    
    def test_empty(self):
        buff = gtk.TextBuffer()
        buff.set_text("")
        indent_selected(buff, "\t")
        self.checkSelected(buff, "")

    def test_empty2(self):
        buff = gtk.TextBuffer()
        buff.set_text("ffoo\nbar\n")
        indent_selected(buff, "\t")
        self.checkSelected(buff, "ffoo\nbar\n")

    def test_select_middle(self):
        # In this case we only select the '2'
        # The only iterator should be the begining of the first line
        buff = gtk.TextBuffer()
        buff.set_text("123\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(1)
        buff.select_range(start_iter, end_iter)
        
        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\nbar\ngaz")

    def test_middle_line2(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("123\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        buff.select_range(start_iter, end_iter)

        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\n\tbar\ngaz")

    def test_skip_line(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\n", buff.get_text(*buff.get_selection_bounds()))
        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\n\nbar\ngaz")
        
    def test_skip_first_line(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        end_iter = start_iter.copy()
        end_iter.forward_chars(3)
        buff.select_range(start_iter, end_iter)
        self.assertEquals("\n\nb", buff.get_text(*buff.get_selection_bounds()))
        indent_selected(buff, "\t")
        self.checkSelected(buff, "\n\n\tbar\ngaz")

    def test_skip_middle_line(self):
        # In this case we select the '23' an empty line and a 'b'
        # The first iterator should be the begining of the first line
        # The second iterator should be the begining of the third line
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(5)
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\nb", buff.get_text(*buff.get_selection_bounds()))

        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\n\n\tbar\ngaz")

    def test_skip_middle_line2(self):
        buff = gtk.TextBuffer()
        buff.set_text("123\nbar\n\ngaz")
        start_iter = buff.get_start_iter()
        end_iter = start_iter.copy()
        end_iter.forward_chars(9)
        # Selected the first two lines
        buff.select_range(start_iter, end_iter)
        self.assertEquals("123\nbar\n\n", buff.get_text(*buff.get_selection_bounds()))

        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\n\tbar\n\ngaz")


    def test_full(self):
        # In this case we select the '23' an empty line and a 'b'
        # The first iterator should be the begining of the first line
        # The second iterator should be the begining of the third line
        buff = gtk.TextBuffer()
        buff.set_text("123\n\nbar\ngaz")
        start_iter, end_iter = buff.get_bounds()
        buff.select_range(start_iter, end_iter)
        self.assertEquals("123\n\nbar\ngaz", buff.get_text(*buff.get_selection_bounds()))
        
        indent_selected(buff, "\t")
        self.checkSelected(buff, "\t123\n\n\tbar\n\tgaz")
        

class TestUnindentSelected(unittest.TestCase):
    def checkSelected(self, buff, text):
        self.assertEquals(text, buff.get_text(*buff.get_bounds()))
    
    def test_empty(self):
        buff = gtk.TextBuffer()
        buff.set_text("")
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "")

    def test_empty2(self):
        # Because the carret is on the start of the file the first
        # tab must be removed.
        buff = gtk.TextBuffer()
        buff.set_text("\tffoo\nbar\n")
        # Move the carret to the begining of the text
        start_iter = buff.get_start_iter()
        buff.move_mark(buff.get_insert(), start_iter)
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "ffoo\nbar\n")

    def test_select_middle(self):
        # In this case we only select the '2'
        # The only iterator should be the begining of the first line
        buff = gtk.TextBuffer()
        buff.set_text("\t123\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(1)
        buff.select_range(start_iter, end_iter)
        
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\n\tbar\ngaz")

    def test_middle_line2(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("\t123\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(6)
        # '23\n\tb'
        buff.select_range(start_iter, end_iter)

        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\nbar\ngaz")

    def test_middle_line3(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("123\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(5)
        # '23\n\tb'
        buff.select_range(start_iter, end_iter)

        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\nbar\ngaz")

    def test_middle_line4(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("\t\t123\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(6)
        # '23\n\tb'
        buff.select_range(start_iter, end_iter)

        unindent_selected(buff, "\t\t")
        self.checkSelected(buff, "123\nbar\ngaz")

    def test_middle_line5(self):
        # In this case we only select the '23\nb'
        # The first iterator should be the begining of the first line
        # The second should be the begining of the second line
        buff = gtk.TextBuffer()
        buff.set_text("\t\t123\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(1)
        end_iter = start_iter.copy()
        end_iter.forward_chars(5)
        # '23\n\tb'
        buff.select_range(start_iter, end_iter)

        unindent_selected(buff, "\t\t")
        self.checkSelected(buff, "123\n\tbar\ngaz")

    def test_skip_line(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("\t123\n\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(2)
        end_iter = start_iter.copy()
        end_iter.forward_chars(4)
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\n", buff.get_text(*buff.get_selection_bounds()))
        
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\n\n\tbar\ngaz")
        
    def test_skip_line2(self):
        # In this case we only select the '23' and an empty line
        # The first iterator should be the begining of the first line
        # It must be the only iterator there
        buff = gtk.TextBuffer()
        buff.set_text("\t123\n\n\tbar\ngaz")
        start_iter = buff.get_start_iter()
        start_iter.forward_chars(2)
        end_iter = start_iter.copy()
        end_iter.forward_chars(5)
        buff.select_range(start_iter, end_iter)
        self.assertEquals("23\n\n\t", buff.get_text(*buff.get_selection_bounds()))
        
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\n\nbar\ngaz")

    def test_full(self):
        # In this case we select the '23' an empty line and a 'b'
        # The first iterator should be the begining of the first line
        # The second iterator should be the begining of the third line
        buff = gtk.TextBuffer()
        buff.set_text("\t123\n\n\tbar\n\tgaz")
        start_iter, end_iter = buff.get_bounds()
        buff.select_range(start_iter, end_iter)
        self.assertEquals("\t123\n\n\tbar\n\tgaz", buff.get_text(*buff.get_selection_bounds()))
        
        unindent_selected(buff, "\t")
        self.checkSelected(buff, "123\n\nbar\ngaz")
    
    def test_chomp(self):
        """This test verifies if unindent eats characters or not"""
        def checkUnindent(src, dst):
            buff = gtk.TextBuffer()
            buff.set_text(src)
            buff.select_range(*buff.get_bounds())
            unindent_selected(buff, "    ")
            self.assertEquals(dst, buff.get_text(*buff.get_bounds()))
        
        checkUnindent("foo", "foo")
        checkUnindent(" foo", "foo")
        checkUnindent("  foo", "foo")
        checkUnindent("   foo", "foo")
        checkUnindent("    foo", "foo")
        checkUnindent(" " * 5 + "foo", " " * 1 + "foo")
        checkUnindent(" " * 6 + "foo", " " * 2 + "foo")
        checkUnindent(" " * 7 + "foo", " " * 3 + "foo")
        checkUnindent(" " * 8 + "foo", " " * 4 + "foo")
        

# TODO: when the text is indented the start should move back to the start of the
# of the line
# and the end should finish on the end of the line

if __name__ == '__main__':
    unittest.main()