# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.



import gtk

from pida.core.environment import get_pixmap_path

pida_icon = gtk.Image()
pida_icon.set_from_file(get_pixmap_path('pida-icon.png'))

class FirstTimeWindow(object):

    def __init__(self, editors):
        self.win = gtk.Dialog(parent=None,
                              title='PIDA First Run Wizard',
                              buttons=(gtk.STOCK_QUIT, gtk.RESPONSE_REJECT,
                                       gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        hbox = gtk.HBox(spacing=12)
        hbox.set_border_width(12)
        self.win.vbox.pack_start(hbox)
        logo = gtk.Image()
        logofrm = gtk.Alignment(0, 0, 0.1, 0.1)
        logofrm.add(pida_icon)
        hbox.pack_start(logofrm, padding=8)
        box = gtk.VBox()
        hbox.pack_start(box, padding=8)
        s = ('It seems this is the first time '
            'you are running Pida.\n\n<b>Please select an editor:</b>')
        l = gtk.Label()
        l.set_markup(s)
        box.pack_start(l, expand=False, padding=8)
        self.radio = gtk.RadioButton()
        self.editors = {}
        for editor in editors:
            self.editors[editor.get_label_cls()] = editor.get_name_cls()
            ebox = gtk.HBox(spacing=6)
            box.pack_start(ebox, expand=False, padding=4)
            radio = gtk.RadioButton(self.radio, label=editor.get_label_cls())
            ebox.pack_start(radio)
            cbox = gtk.VBox(spacing=3)
            label = gtk.Label()
            label.set_alignment(1, 0.5)
            cbox.pack_start(label)
            ebox.pack_start(cbox, padding=4, expand=False)
            sanitybut = gtk.Button(label='Check')
            ebox.pack_start(sanitybut, expand=False, padding=1)
            sanitybut.connect('clicked', self.cb_sanity, editor, radio, label)
            self.cb_sanity(sanitybut, editor, radio, label)
            self.radio = radio
        bbox = gtk.HBox()
        box.pack_start(bbox, expand=False, padding=4)

    def run(self, filename):
        self.win.show_all()
        response = self.win.run()
        self.win.hide_all()
        editor_name = self.get_editor_option()
        self.win.destroy()
        # Only write the token file if we want the user chose something
        success = (response == gtk.RESPONSE_ACCEPT)
        if success:
            self.write_file(filename)
        return (success, editor_name)

    def cb_sanity(self, button, component, radio, label):
        errs =  component.get_sanity_errors()

        if errs:
            radio.set_sensitive(False)
            radio.set_active(False)
            s = '\n'.join(errs)
            label.set_markup('<span size="small" foreground="#c00000">'
                             '<i>%s</i></span>' % s)
        else:
            radio.set_sensitive(True)
            radio.set_active(True)
            label.set_markup('<span size="small" foreground="#00c000">'
                             '<i>Okay to use</i></span>')
            button.set_sensitive(False)

    def get_editor_option(self, *args):
        for radio in self.radio.get_group():
            if radio.get_active():
                editor = radio.get_label()
                return self.editors[editor]

    def write_file(self, filename):
        f = open(filename, 'w')
        f. write('#Remove this to rerun the start wizard\n\n')
        f.close()

if __name__ == '__main__':
    ftw = FirstTimeWindow([])
    print ftw.run('/home/ali/firstrun')







# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
