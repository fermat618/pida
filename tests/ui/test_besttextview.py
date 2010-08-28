
import gtk
import gtk.gdk

from pida.services.language import DOCTYPES
from pida.utils.testing import refresh_gui


class BaseTests(object):

    def setUp(self):
        self.textview = self.TextView()

    def setup_method(self, method):
        self.setUp()

    def test_setget_text(self):
        txt = 'some text to test with\nwith two lines'
        self.textview.get_buffer().set_text(txt)
        print txt
        assert txt == self.textview.get_buffer().props.text
        txt = u'some \u1234text to test \u4321 with\nwith two lines'
        self.textview.get_buffer().set_text(txt)
        print txt
        assert txt == self.textview.get_buffer().props.text

    def test_sethighligting(self):
        assert self.textview.get_doctype() is None

        self.textview.set_doctype(DOCTYPES['Python'])
        assert self.textview.get_doctype() == DOCTYPES['Python']
        #if self.textview.has_syntax_highlighting:
        #    self.assertNotEqual(self.textview.get_lang(), None)

    def test_readonly(self):
        txt = 'some text to test with\nwith two lines'
        win = gtk.Window()
        win.add(self.textview)
        win.show_all()
        for do in (True, False):
            self.textview.get_buffer().set_text(txt)
            self.textview.set_editable(do)

            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = gtk.keysyms.a
            #event.state = gtk.gdk.SHIFT_MASK
            event.window = self.textview.window

            #widget.emit('key-press-event', event)

            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = gtk.keysyms.a

            buffer_ = self.textview.get_buffer()
            buffer_.place_cursor(buffer_.get_iter_at_offset(0))
            #self.textview.do_event(self.textview, event)
            self.textview.emit('key-press-event', event)
            refresh_gui()
            if do:
                assert self.textview.get_buffer().props.text == "a%s" % txt
            else:
                assert self.textview.get_buffer().props.text == txt
        win.destroy()
try:
    from pida.ui.besttextview.mooview import MooTextView
    class TestMoo(BaseTests):
        TextView = MooTextView

except ImportError:
    #FIXME: how to report skipped tests properly ???
    print "can't import moo, skipping MooTextView tests"

try:
    from pida.ui.besttextview.sourceview import SourceTextView

    class TestSourceView(BaseTests):
        TextView = SourceTextView

except ImportError:
    #FIXME: how to report skipped tests properly ???
    print "can't import gtksourceview, skipping SourceView tests"


from pida.ui.besttextview.textview import SimpleTextView

class TestSimpleText(BaseTests):
    TextView = SimpleTextView

