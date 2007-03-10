__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import unittest
import gwp
import gconf
import gtk

GCONF_KEY = "/apps/gwp/key_str"

class TestGConfValue(unittest.TestCase):
    def setUp(self):
        self.gconf = gconf.client_get_default().add_dir("/apps/gwp", gconf.CLIENT_PRELOAD_NONE)
        self.value = gwp.GConfValue(
          key = GCONF_KEY,
          data_spec = gwp.Spec.STRING
        )
        
    def test_set_default(self):
        self.assertEqual(self.value.data_spec, gwp.Spec.STRING)
        self.assertEqual(self.value.default, self.value.data_spec.default)
        self.value.default = "default"
        self.assertEqual(self.value.default, "default")
        self.value.data = self.value.default
        self.assertEqual(self.value.client.get_string(self.value.key), self.value.default)
        self.assertEqual(self.value.data, self.value.default)
    
    def test_set_data(self):
        self.value.data = self.value.default

        self.value.data = "foo"
        self.assertEqual(self.value.client.get_string(self.value.key), "foo")
        self.assertEqual(self.value.data, "foo")
    
    def callback1(self, *args):
        self.assertTrue(self.value.data, "bar")
        self.foo = True
        gtk.main_quit()
    
    def test_set_callback(self):
        self.value.data = self.value.default
        self.foo = False
        self.value.set_callback(self.callback1)
        self.value.data = "bar"
        gtk.main()
        self.assertTrue(self.foo)
    
    def test_default(self):
        self.assertEqual(self.value.default, "")
        self.value.default = "var"
        self.assertEqual(self.value.default, "var")
        self.value.reset_default()
        self.assertEqual(self.value.default, "")


class TestDataEntry(unittest.TestCase):
    def setUp(self):
        self.entry = gtk.Entry()
        self.entry.set_text("foo")
        self.value = gwp.create_persistency_link(self.entry, GCONF_KEY)
        
    def test_unset_data(self):
        # First we make sure the integrity exists upon start
        self.assertEqual(self.entry.get_text(), self.value.data)
        self.assertEqual(self.value.storage.data, self.value.data)
        

    def test_widget_to_gconf(self):
        """From widget to gconf entry"""
        
        self.entry.set_text("bar")
        self.assertEqual(self.value.data, "bar")

    def test_gconf_to_widget(self):
        """From gconf to widget"""
        self.value.data = "foo"
        self.assertEqual(self.entry.get_text(), "foo")
    
    
    def test_destroy_widget(self):
        self.entry.destroy()
        assert self.value.widget is None
    
    def test_widget_signal(self):
        pass
    
    def test_gconf_signal(self):
        pass
    
    def test_gconf_disabled(self):
        pass
    
    def test_sync_widget(self):
        pass
    
    def test_sync_gconf(self):
        pass

class TestDataCheckbutton(unittest.TestCase):
    def setUp(self):
        self.entry = gtk.CheckButton()
        self.entry.set_active(True)
        self.value = gwp.create_persistency_link(self.entry, GCONF_KEY)

    def test_unset_data(self):
        # First we make sure the integrity exists upon start
        self.assertEqual(self.entry.get_active(), self.value.data)
        self.assertEqual(self.value.storage.data, self.value.data)
        
    def test_widget_to_gconf(self):
        """From widget to gconf entry"""
        
        self.entry.set_active(False)
        self.assertEqual(self.value.data, False)

    def test_gconf_to_widget(self):
        """From gconf to widget"""
        self.value.data = False
        self.assertEqual(self.entry.get_active(), False)
    
    
    def test_destroy_widget(self):
        self.entry.destroy()
        assert self.value.widget is None
    
    def test_widget_signal(self):
        pass
    
    def test_gconf_signal(self):
        pass
    
    def test_gconf_disabled(self):
        pass
    
    def test_sync_widget(self):
        pass
    
    def test_sync_gconf(self):
        pass


class TestToggleButton(TestDataCheckbutton):
    def setUp(self):
        self.entry = gtk.ToggleButton()
        self.entry.set_active(True)
        self.value = gwp.create_persistency_link(self.entry, GCONF_KEY)



class TestSpinButton(unittest.TestCase):
    def setUp(self):
        self.entry = gtk.CheckButton()
        self.entry.set_active(True)
        self.value = gwp.create_persistency_link(self.entry, GCONF_KEY)

    def test_unset_data(self):
        # First we make sure the integrity exists upon start
        self.assertEqual(self.entry.get_active(), self.value.data)
        self.assertEqual(self.value.storage.data, self.value.data)
        
    def test_widget_to_gconf(self):
        """From widget to gconf entry"""
        
        self.entry.set_active(False)
        self.assertEqual(self.value.data, False)

    def test_gconf_to_widget(self):
        """From gconf to widget"""
        self.value.data = False
        self.assertEqual(self.entry.get_active(), False)
    
    
    def test_destroy_widget(self):
        self.entry.destroy()
        assert self.value.widget is None
    
    def test_widget_signal(self):
        pass
    
    def test_gconf_signal(self):
        pass
    
    def test_gconf_disabled(self):
        pass
    
    def test_sync_widget(self):
        pass
    
    def test_sync_gconf(self):
        pass


class TestRadioButtonData:
    def test_unset_data(self):
        pass
    
    def test_set_data(self):
        pass
    
    def test_destroy_widget(self):
        pass
    
    def test_widget_signal(self):
        pass
    
    def test_gconf_signal(self):
        pass
    
    def test_gconf_disabled(self):
        pass
    
    def test_sync_widget(self):
        pass
    
    def test_sync_gconf(self):
        pass
    
def main():
    unittest.main()

if __name__ == '__main__':
    main()