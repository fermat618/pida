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


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView
from pida.ui.widgets import get_widget_for_type

from kiwi import ValueUnset

def service_sort_func(s1, s2):
    return cmp(s1.get_label(), s2.get_label())

class PidaOptionsView(PidaGladeView):

    gladefile = 'options-editor'

    def create_ui(self):
        self._services = []
        for svc in self.svc.boss.get_services():
            if len(svc.get_options()):
                self._services.append(svc)
        self._services.sort(service_sort_func)
        self._services_display = []
        for svc in self._services:
            self._add_service(svc)
        self.service_combo.prefill(self._services_display)
        self.options_book.show_all()

    def _add_service(self, svc):
        self._services_display.append((svc.get_label(), svc))
        self.options_book.append_page(self._create_page(svc))
        
    def _create_page(self, svc):
        mainvb = gtk.VBox(spacing=0)
        mainvb.set_border_width(6)
        label = gtk.Label()
        label.set_markup('<big><b>%s</b></big>' % svc.get_label())
        label.set_alignment(0, 0.5)
        mainvb.pack_start(label, expand=False)
        optvb = gtk.VBox()
        optsw = gtk.ScrolledWindow()
        optsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        optvb.set_border_width(6)
        optsw.add_with_viewport(optvb)
        mainvb.pack_start(optsw)
        labelsizer = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        widgetsizer = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        for opt in svc.get_options().iter_options():
            vb = gtk.VBox(spacing=2) 
            vb.set_border_width(6)
            optvb.pack_start(vb, expand=False)
            hb = gtk.HBox(spacing=6)
            vb.pack_start(hb)
            optlabel = gtk.Label()
            optlabel.set_text(opt.label)
            optlabel.set_alignment(0, 0.5)
            labelsizer.add_widget(optlabel)
            hb.pack_start(optlabel, expand=False)
            optwidget = get_widget_for_type(opt.rtype)
            widgetsizer.add_widget(optwidget)
            hb.pack_start(optwidget, expand=True)
            optwidget.update(opt.get_value())
            optwidget.connect('content-changed', self._on_option_changed, opt)
            opt.add_notify(self._on_option_changed_elsewhere, optwidget)
            doclabel = gtk.Label()
            doclabel.set_text(opt.doc)
            doclabel.set_alignment(0, 0)
            vb.pack_start(doclabel)
        return mainvb

    def on_service_combo__content_changed(self, cmb):
        svc = self.service_combo.read()
        pagenum = self._services.index(svc)
        self.options_book.set_current_page(pagenum)

    def _on_option_changed(self, widget, option):
        widgval = widget.read()
        optval = option.get_value()
        # various hacks
        if widgval is None:
            return
        if widgval == ValueUnset:
            widgval = ''
        if widgval != optval:
            option.set_value(widgval)

    def _on_option_changed_elsewhere(self, client, id, entry, (option, widget)):
        widget.update(option.get_value())
            


class OptionsActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_options',
            TYPE_TOGGLE,
            'Edit Preferences',
            'Edit the PIDA preferences',
            'properties',
            self.on_show_options,
            '<Shift><Control>asciitilde'
        )

    def on_show_options(self, action):
        if action.get_active():
            self.svc.show_options()
        else:
            self.svc.hide_options()

# Service class
class Optionsmanager(Service):
    """Describe your Service Here""" 

    actions_config = OptionsActions

    def start(self):
        self._view = PidaOptionsView(self)

    def show_options(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_options(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

# Required Service attribute for service loading
Service = Optionsmanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
