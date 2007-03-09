
import threading

import gtk
import gobject

from cgi import escape
from gtk import gdk

gdk.threads_init()

import lplib as launchpadlib

busy_cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
normal_cursor = gtk.gdk.Cursor(gtk.gdk.RIGHT_PTR)

TITLE_MARKUP = '<span size="xx-large">Make a launchpad bug report</span>'

def label_widget(widget, label):
    vb = gtk.VBox()
    vb.set_border_width(6)
    label = gtk.Label(label)
    label.set_alignment(0, 0.5)
    vb.pack_start(label, expand=False)
    exp = isinstance(widget, gtk.ScrolledWindow)
    vb.pack_start(widget, expand=exp)
    return vb


class PasswordDialog(gtk.Dialog):
    def __init__(self):
        super(PasswordDialog, self).__init__('Enter User Details',
            parent = None,
            flags = 0,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                       gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.email = gtk.Entry()
        self.password = gtk.Entry()
        self.password.set_visibility(False)
        self.vbox.pack_start(label_widget(self.email, 'Email Address'))
        self.vbox.pack_start(label_widget(self.password, 'Password'))
        self.save_details = gtk.CheckButton()
        self.save_details.set_label('Save across sessions?')
        self.vbox.pack_start(self.save_details)
        self.show_all()

    def get_user_details(self):
        return (self.email.get_text(), self.password.get_text(),
                self.save_details.get_active())



class ReportWidget(gtk.VBox):

    def __init__(self, opts):
        super(ReportWidget, self).__init__()
        self.product = gtk.Entry()
        exp = gtk.Expander('Details')
        vb = gtk.VBox()
        exp.add(vb)
        if opts.show_product:
            prod_container = self
        else:
            prod_container = vb
        prod_container.pack_start(label_widget(self.product, 'Product'), False)
        self.title = gtk.Entry()
        self.pack_start(label_widget(self.title, 'Title'), False)
        self.comment = gtk.TextView()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.comment)
        self.pack_start(label_widget(sw, 'Comment'))
        self.pack_start(exp, expand=False)
        self.baseurl = gtk.Entry()
        #vb.pack_start(label_widget(self.baseurl, 'Launchpad URL'), False)
        self.pulser = gtk.ProgressBar()
        self.pulser.set_no_show_all(True)
        self.pack_start(self.pulser, expand = False)
        self.baseurl.set_text(opts.root_url)
        self.product.set_text(opts.product)
        buf = self.comment.get_buffer()
        buf.insert(buf.get_start_iter(), opts.comment)
        self.title.set_text(opts.title)
        self.email, self.password = launchpadlib.get_local_config()
        self._pulsing = False
    
    def start_pulsing(self):
        self._pulsing = True
        self.pulser.show()
        def _pulse():
            self.pulser.pulse()
            return self._pulsing
        gobject.timeout_add(100, _pulse)
    
    def stop_pulsing(self):
        self._pulsing = False
        self.pulser.hide()
    
    def report(self, finished_callback=lambda r: None):
        if self.email is None:
            self.get_pass()
        if self.email is None:
            return
        buf = self.comment.get_buffer()
        self.start_pulsing()
        def report():
            product = self.product.get_text()
            
            results = launchpadlib.report(
                        self.baseurl.get_text(),
                        self.email, self.password,
                        product,
                        self.title.get_text(),
                        buf.get_text(buf.get_start_iter(), buf.get_end_iter()))
                
            gobject.idle_add(self.stop_pulsing)
            gobject.idle_add(finished_callback, results)

        threading.Thread(target=report).start()
    
    def get_pass(self):
        pass_dlg = PasswordDialog()
        def pass_response(dlg, resp):
            dlg.hide()
            if resp == gtk.RESPONSE_ACCEPT:
                self.email, self.password, save = dlg.get_user_details()
                if save:
                    launchpadlib.save_local_config(self.email, self.password)
            dlg.destroy()
        pass_dlg.connect('response', pass_response)
        pass_dlg.run()
      
        

class ReportWindow(gtk.Dialog):
    
    def __init__(self, opts):
        super(ReportWindow, self).__init__('Launchpad Bug Report',
            parent = None,
            flags = 0,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                       gtk.STOCK_OK, gtk.RESPONSE_OK))
        self._reporter = ReportWidget(opts)
        self.vbox.pack_start(self._reporter)
        self.resize(400, 300)
        gobject.idle_add(self._reporter.title.grab_focus)
    
import rat.hig

class GuiReport:
    def __init__(self, opts, do_quit=True):
        self.opts = opts
        self.do_quit = do_quit
    
    def set_command_sensitive(self, sensitive):
        self.w.set_response_sensitive(gtk.RESPONSE_OK, sensitive)
        self.w._reporter.set_sensitive(sensitive)
        
    def on_err_response(self, dlg, response):
        dlg.destroy()
        
    def on_report_finished(self, results):
        success, results = results
        if not success:
            title = "Could not report error"
            msg = ("There was an error "
                   "comunicating with the server. Please verify your "
                   "username and password. The error was %s" %
                    escape(str(results)))
            dlgfact = rat.hig.error 
        else:
            title = 'Successfully reported Bug'
            msg = ('Bug successfully reported to launchpad at: %s' % results)
            dlgfact = rat.hig.info
        dlg = dlgfact(title, msg, parent = self.w, run=False)
        dlg.show_all()
        dlg.connect("response", self.on_err_response)
        if success:
            self.stop()
        else:
            self.set_command_sensitive(True)
    
    def on_report_window_response(self, dlg, response):
        if response == gtk.RESPONSE_OK:
            self.set_command_sensitive(False)
            dlg._reporter.report(self.on_report_finished)
        else:
            self.stop()
    
    def stop(self):
        self.w.destroy()
        if self.do_quit:
            gtk.main_quit()

    def start(self):
        self.w = w = ReportWindow(self.opts)
        w.show_all()
        w.connect('response', self.on_report_window_response)

def gui_report(opts):
    gobject.idle_add(GuiReport(opts).start)
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
    
    
