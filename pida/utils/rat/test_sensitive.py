__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import gtk
import unittest
#from rat import sensitive
import sensitive

class TestCounter(unittest.TestCase):
    
    
    def setUp(self):
        self.amount = 0
        
    def cb(self, amount):
        self.amount = amount
    
    def test_counter(self):
        counter = sensitive.Counter(self.cb)

        counter.inc()
        self.assertEqual(self.amount, 1)

        counter.inc()
        self.assertEqual(self.amount, 2)
        
        counter.dec()
        self.assertEqual(self.amount, 1)

        counter.dec()
        self.assertEqual(self.amount, 0)

        counter.dec()
        self.assertEqual(self.amount, -1)

class TestClient(unittest.TestCase):
    def setUp(self):
        self.amount = 0
        self.counter = sensitive.Counter(self.cb)
        
    def cb(self, amount):
        self.amount = amount

    def test_client(self):
        # When we create a client the amount is at 0
        self.assertEqual(self.amount, 0)
        client = sensitive.SensitiveClient(self.counter)
        self.assertEqual(self.amount, 0)
        
        # Setting it to Sensitive should maintain it to 0
        client.set_sensitive(True)
        self.assertEqual(self.amount, 0)
        
        # Setting it again does nothing
        client.set_sensitive(True)
        self.assertEqual(self.amount, 0)
        
        # Setting it to false makes it go to 1
        client.set_sensitive(False)
        self.assertEqual(self.amount, 1)
        
        # Setting it again, makes nothing
        client.set_sensitive(False)
        self.assertEqual(self.amount, 1)

        # Setting it to Sensitive should maintain it to 0 again
        client.set_sensitive(True)
        self.assertEqual(self.amount, 0)
        
        # Setting it to insensitive and removing its reference should make
        # the amount back to 1
        client.set_sensitive(False)
        self.assertEqual(self.amount, 1)
        client = None
        self.assertEqual(self.amount, 0)
        
class TestController(unittest.TestCase):
    
    def setUp(self):
        self.lbl = gtk.Label()
        self.cnt = sensitive.SensitiveController(self.lbl)
    
    def is_sensitive(self):
        return self.lbl.get_property("sensitive")
    
    def test_0_controller_ref(self):
        # If the label is insensitive and we loose our controller's ref
        # __del__ will set the sensitive back to True
        self.lbl.set_sensitive(False)
        self.cnt = None
        self.assertTrue(self.is_sensitive())
        
        # When we create a controller then it should make the associated
        # widget sensitive
        self.lbl.set_sensitive(False)
        self.cnt = sensitive.SensitiveController(self.lbl)
        self.assertTrue(self.is_sensitive())
        
        # In this test we'll register an affecter and make it insensitive
        # After this we'll loose the reference to our controller, this
        # should make the 'self.lbl' sensitive again
        client = self.cnt.create_client()
        client.set_sensitive(False)
        self.failIf(self.is_sensitive())
        self.cnt = None
        self.assertTrue(self.is_sensitive())

    def test_1_client(self):
        
        # A widget starts as sensitive
        self.assertTrue(self.is_sensitive())
        
        # When we register it it maintains sensitive
        client = self.cnt.create_client()
        self.assertTrue(self.is_sensitive())
        
        # Since we only have one registred client, which is self
        # setting it to False will make the widget not sensitive too
        client.set_sensitive(False)
        self.failIf(self.is_sensitive())
        
        # Making it sensitive again will also affect global sensitive status
        client.set_sensitive(True)
        self.assertTrue(self.is_sensitive())
        
        # Setting it back to False and removing the client will
        # reset the sensitive status back to True
        client.set_sensitive(False)
        self.failIf(self.is_sensitive())
        client = None
        self.assertTrue(self.is_sensitive())
    
    def test_destroy_object(self):
        client = self.cnt.create_client()
        self.lbl.destroy()
        
    
    def test_2_signal_bind(self):
        # We'll bind the 'text' property of the 'gtk.Entry'
        # through the signal 'changed' to make the 'self.lbl' sensitive when
        # its text is empty 
        entry = gtk.Entry()
        bind = sensitive.SignalBind(self.cnt)
        
        bind.bind(
            entry,
            "text",
            "changed",
            lambda text: text != ""
        )
        
        # Since the bind has effect once the instance is created and the text
        # on the 'gtk.Entry' starts empty then it 
        # should make our label insensitive
        self.failIf(self.is_sensitive())
        
        # Changing the text to something else
        entry.set_text("Foo")
        self.assertTrue(self.is_sensitive())
        
        # Clearing the text entry again
        entry.set_text("")
        self.failIf(self.is_sensitive())
        
        # If we loose the reference to the 'bind' object then the connection
        # should be terminated, which means it should be sensitive again
        bind = None
        self.assertTrue(self.is_sensitive())


def main():
    unittest.main()

if __name__ == '__main__':
    main()

