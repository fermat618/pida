# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

from textwrap import wrap

import gtk

# PIDA Imports
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_TOGGLE

from pida.ui.views import PidaGladeView
from pida.ui.widgets import get_widget_for_type, get_proxy_for_widget


# locale
from pida.core.locale import Locale
locale = Locale('optionsmanager')
_ = locale.gettext



class OptionsPage(gtk.VBox):
    #XXX: this should be a slaveview
    #     it should try to use the options.ui from a service
    #     and add other items below
    def __init__(self, view, svc):
        gtk.VBox.__init__(self, spacing=0)
        self.set_border_width(6)

        self.view = view
        self.svc = svc
        self.widgets = {}
        self.proxies = {}

        label = gtk.Label()
        label.set_markup('<big><b>%s</b></big>' % svc.get_label())
        label.set_alignment(0, 0.5)

        self.pack_start(label, expand=False)

        optsw = gtk.ScrolledWindow()
        optsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        optvb = gtk.VBox()
        optvb.set_border_width(6)

        optsw.add_with_viewport(optvb)

        self.pack_start(optsw)

        labelsizer = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        widgetsizer = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        for opt in sorted(svc.options):
            vb = gtk.VBox(spacing=2)
            vb.set_border_width(6)

            eb = gtk.EventBox()
            eb.add(vb)

            optvb.pack_start(eb, expand=False)

            hb = gtk.HBox(spacing=6)
            vb.pack_start(hb)

            optlabel = gtk.Label()
            lbl = opt.label
            doc = opt.doc
            if opt.workspace:
                lbl += " *"
                doc += "\n(bound to workspace)"
            optlabel.set_text('\n'.join(wrap(lbl, 20)))
            optlabel.set_alignment(0, 0)
            labelsizer.add_widget(optlabel)
            hb.pack_start(optlabel, expand=False)

            opt_widget = get_widget_for_type(opt.type)
            opt_proxy = get_proxy_for_widget(opt_widget)
            opt_proxy.connect_widget()
            widgetsizer.add_widget(opt_widget)
            hb.pack_start(opt_widget, expand=True)
            opt_proxy.update(opt.value)
            opt_proxy.connect('changed', self._on_option_changed, opt)
            self.widgets[opt.name] = opt_widget
            self.proxies[opt.name] = opt_proxy
            view._tips.set_tip(eb, doc)

    def _on_option_changed(self, proxy, value, option):
        optval = option.value
        # various hacks
        if value is None:
            return
        if value != optval:
            option.group.set_value(option.name, value)

    def _on_option_changed_elsewhere(self, option):
        widgval = self.proxies[option.name].read()
        optval = option.value
        if optval != widgval:
            self.proxies[option.name].update(option.value)

class PidaOptionsView(PidaGladeView):

    key = 'optionsmanager.editor'

    locale = locale
    label_text = 'Preferences'

    icon_name = 'gnome-settings'

    def create_ui(self):
        self.service_list = gtk.ListStore(str, object)
        self.service_combo = gtk.ComboBox(self.service_list)
        self.service_proxy = get_proxy_for_widget(self.service_combo)
        self.service_proxy.connect_widget()
        renderer = gtk.CellRendererText()
        self.service_combo.pack_start(renderer)
        self.service_combo.add_attribute(renderer, 'text', 0)

        self.options_book = ob = gtk.Notebook()
        ob.set_property('width-request',400)
        ob.set_property('border-width', 6)
        ob.set_property('show_tabs', False)

        self.widget.pack_start(self.service_combo, expand=False)
        self.widget.pack_start(ob)
        self.widget.show_all()
        self.svc.events.subscribe('option_changed',
                                  self._on_option_changed_elsewhere)
        self.current = None

        self.refresh_ui()

    def clear_ui(self):
        while self.options_book.get_n_pages():
            self.options_book.remove_page(-1)
        self._service_pages = {}
        self._service_page_widgets = {}
        self._services = []
        self.service_list.clear()

    def refresh_ui(self):
        current = self.current
        self.clear_ui()

        for svc in self.svc.boss.get_services():
            if svc.options:
                self._services.append(svc)
                self.service_list.append(
                    (svc.get_label(), svc),
                )

        self._services.sort(key=Service.sort_key)

        self._tips = gtk.Tooltips()
        if current:
            self.service_proxy.update(current)


        if current is not None:
            try:
                self.service_proxy.update(current)
            except KeyError:
                self.service_proxy.update(self.current)

    def _add_service(self, svc):
        self._service_pages[svc.get_name()] = self.options_book.get_n_pages()
        page = OptionsPage(self, svc)
        self._service_page_widgets[svc.get_name()] = page
        self.options_book.append_page(page)
        self.options_book.show_all()

    def on_service_proxy__changed(self, p, svc):
        self.current = svc
        if not svc:
            return # no service was selected
        if not svc.get_name() in self._service_pages:
            self._add_service(svc)
        pagenum = self._service_pages[svc.get_name()]
        self.options_book.set_current_page(pagenum)


    def _on_option_changed_elsewhere(self, option):
        page = self._service_page_widgets.get(option.group.svc.get_name())
        if page is not None:
            page._on_option_changed_elsewhere(option)

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

    def create(self):
        self.publish('option_changed')

    def subscribe_all_foreign(self):
        self.subscribe_foreign('plugins', 'plugin_started',
                               self.plugin_changed)
        self.subscribe_foreign('plugins', 'plugin_stopped',
                               self.plugin_changed)

    def plugin_changed(self, plugin):
        self.svc.refresh_view()

# Service class
class Optionsmanager(Service):
    """Describe your Service Here""" 

    actions_config = OptionsActions
    events_config = OptionsEvents

    def start(self):
        self._view = PidaOptionsView(self)

    def show_options(self):
        self._view.refresh_ui()
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_options(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def refresh_view(self):
        self._view.refresh_ui()

# Required Service attribute for service loading
Service = Optionsmanager



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
