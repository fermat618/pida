# -*- coding: utf-8 -*- 
"""
    The dialog thats shown on the first run

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import os
import gtk
import pida

pida_icon = gtk.Image()
pida_icon.set_from_file(os.path.join(
    pida.__path__[0],
    'resources/pixmaps/pida-icon.png'))

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
            self.editors[editor.get_label()] = editor.get_name()
            ebox = gtk.HBox(spacing=6)
            box.pack_start(ebox, expand=False, padding=4)
            radio = gtk.RadioButton(self.radio, label=editor.get_label())
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
    from pida.editors.vim.vim import Vim
    from pida.editors.mooedit.mooedit import Mooedit
    ftw = FirstTimeWindow([Vim, Mooedit])
    print ftw.run('~/firstrun')







# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
