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

from cgi import escape

import gtk
import gobject


# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView

from pida.utils.launchpadder.gtkgui import PasswordDialog
from pida.utils.launchpadder.lplib import save_local_config, get_local_config,\
                                          report
from pida.utils.gthreads import AsyncTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('bugreport')
_ = locale.gettext

class BugreportView(PidaGladeView):
    
    gladefile = 'bugreport'
    locale = locale

    icon_name = 'error'
    label_text = _('Bug Report')

    def on_ok_button__clicked(self, button):
        self.email, self.password = get_local_config()
        if self.email is None:
            self.get_pass()
        self.progress_bar.set_text('')
        task = AsyncTask(self.report, self.report_complete)
        task.start()
        self._pulsing = True
        gobject.timeout_add(100, self._pulse)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_bugreport').set_active(False)

    def report(self):
        title = self.title_entry.get_text()
        buf = self.description_text.get_buffer()
        description = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        return report(None, self.email, self.password, 'pida', title, description)

    def report_complete(self, success, data):
        if success:
            self.progress_bar.set_text(_('Bug Reported:\n%s') % data)
        else:
            self.progress_bar.set_text(_('Bug Report Failed:\n%s') % data)
        self._pulsing = False

    def _pulse(self):
        self.progress_bar.pulse()
        return self._pulsing

    def get_pass(self):
        pass_dlg = PasswordDialog()
        def pass_response(dlg, resp):
            dlg.hide()
            if resp == gtk.RESPONSE_ACCEPT:
                self.email, self.password, save = dlg.get_user_details()
                if save:
                    save_local_config(self.email, self.password)
            dlg.destroy()
        pass_dlg.connect('response', pass_response)
        pass_dlg.run()

    def can_be_closed(self):
        self.svc.get_action('show_bugreport').set_active(False)


class BugreportActions(ActionsConfig):
    
    def create_actions(self):
        self.create_action(
            'show_bugreport',
            TYPE_TOGGLE,
            _('Bug report'),
            _('Make a bug report'),
            'error',
            self.on_report,
            '<Shift><Control>b'
        )

    def on_report(self, action):
        if action.get_active():
            self.svc.show_report()
        else:
            self.svc.hide_report()


# Service class
class Bugreport(Service):
    """Describe your Service Here""" 

    actions_config = BugreportActions

    def pre_start(self):
        self._view = BugreportView(self)
    
    def show_report(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)

    def hide_report(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

# Required Service attribute for service loading
Service = Bugreport



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
