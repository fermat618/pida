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

from textwrap import wrap

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

# locale
from pida.core.locale import Locale
locale = Locale('optionsmanager')
_ = locale.gettext

def service_sort_func(s1, s2):
    return cmp(s1.get_label(), s2.get_label())

def options_sort_func(o, o1):
    return cmp(o1.name, o2.name)


class PidaOptionsView(PidaGladeView):

    gladefile = 'options-editor'
    locale = locale
    label_text = 'Preferences'

    icon_name = 'gnome-settings'

    def create_ui(self):
        self.current = None
        self.refresh_ui()

    def clear_ui(self):
        while self.options_book.get_n_pages():
            self.options_book.remove_page(-1)
        self._services_display = []
        self._service_pages = {}

    def refresh_ui(self):
        current = self.current
        self.clear_ui()
        self._services = []
        for svc in self.svc.boss.get_services():
            if len(svc.options):
                self._services.append(svc)
                self._services_display.append(
                    (svc.get_label(), svc),
                )
        self._services.sort(service_sort_func)
        self._tips = gtk.Tooltips()
        self.service_combo.prefill(self._services_display)
        if current is not None:
            try:
                self.service_combo.update(current)
            except KeyError:
                self.service_combo.update(self.current)
                

    def _add_service(self, svc):
        self._service_pages[svc.servicename] = self.options_book.get_n_pages()
        self.options_book.append_page(self._create_page(svc))
        self.options_book.show_all()
        
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
        options = list(svc.options.iter_options())
        options.sort()
        for opt in options:
            vb = gtk.VBox(spacing=2)
            vb.set_border_width(6)
            eb = gtk.EventBox()
            eb.add(vb)
            optvb.pack_start(eb, expand=False)
            hb = gtk.HBox(spacing=6)
            vb.pack_start(hb)
            optlabel = gtk.Label()
            optlabel.set_text('\n'.join(wrap(opt.label, 20)))
            optlabel.set_alignment(0, 0)
            labelsizer.add_widget(optlabel)
            hb.pack_start(optlabel, expand=False)
            optwidget = get_widget_for_type(opt.rtype)
            widgetsizer.add_widget(optwidget)
            hb.pack_start(optwidget, expand=True)
            value = opt.get_value()
            optwidget.update(value)
            optwidget.connect('content-changed', self._on_option_changed, opt)
            opt.add_notify(self._on_option_changed_elsewhere, optwidget)
            self._tips.set_tip(eb, opt.doc)
        return mainvb

    def on_service_combo__content_changed(self, cmb):
        self.current = svc = self.service_combo.read()
        if not svc:
            return # no service was selected
        if not svc.servicename in self._service_pages:
            self._add_service(svc)
        pagenum = self._service_pages[svc.servicename]
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
        widgval = widget.read()
        optval = option.get_value()
        if optval != widgval:
            widget.update(option.get_value())

    def can_be_closed(self):
        self.svc.get_action('show_options').set_active(False)


class OptionsActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_options',
            TYPE_TOGGLE,
            _('Edit Preferences'),
            _('Edit the PIDA preferences'),
            'properties',
            self.on_show_options,
            '<Shift><Control>asciitilde'
        )

    def on_show_options(self, action):
        if action.get_active():
            self.svc.show_options()
        else:
            self.svc.hide_options()

class OptionsEvents(EventsConfig):

    def subscribe_foreign_events(self):
        self.subscribe_foreign_event('plugins', 'plugin_started',
                                     self.plugin_changed)
        self.subscribe_foreign_event('plugins', 'plugin_stopped',
                                     self.plugin_changed)

    def plugin_changed(self, plugin):
        if len(plugin.options):
            self.svc.refresh_view()

# Service class
class Optionsmanager(Service):
    """Describe your Service Here""" 

    actions_config = OptionsActions
    events_config = OptionsEvents

    def start(self):
        self._view = PidaOptionsView(self)

    def show_options(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_options(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def refresh_view(self):
        self._view.refresh_ui()

# Required Service attribute for service loading
Service = Optionsmanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
