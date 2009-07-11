# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""
import sys
from cgi import escape

import gtk
import gobject


# PIDA Imports
import pida

from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.core.environment import on_windows
from pida.ui.views import PidaGladeView

from pida.utils.gthreads import AsyncTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('bugreport')
_ = locale.gettext

class BugreportView(PidaGladeView):

    key = 'bugreport.form'

    gladefile = 'bugreport'
    locale = locale

    icon_name = 'error'
    label_text = _('Bug Report')

    def on_ok_button__clicked(self, button):
        self.get_pass()
        if self.email is None:
            return
        self.progress_bar.set_text('')
        task = AsyncTask(self.report, self.report_complete)
        task.start()
        self._pulsing = True
        self.progress_bar.show()
        gobject.timeout_add(100, self._pulse)

    def on_close_button__clicked(self, button):
        self.svc.get_action('show_bugreport').set_active(False)

    def report(self):
        title = self.title_entry.get_text()
        buf = self.description_text.get_buffer()
        description = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        description = 'PIDA %s\n--\n%s' % (pida.version, description)
        #FIXME causes memleak and deadlock on win32
        if on_windows:
            return
        from pida.utils.launchpadder.lplib import report

        return report(None, self.email, self.password, 'pida', title, description)

    def report_complete(self, success, data):
        if success:
            self.svc.boss.cmd('notify', 'notify', title=_('Bug Reported'), data=data)
            self.title_entry.set_text('')
            self.description_text.get_buffer().set_text('')
            self.svc.boss.cmd('browseweb', 'browse', url=data.strip())
        else:
            self.svc.boss.cmd('notify', 'notify', title=_('Bug Report Failed'), data=data)
        self.progress_bar.hide()
        self._pulsing = False

    def _pulse(self):
        self.progress_bar.pulse()
        return self._pulsing

    def get_pass(self):
        #FIXME causes memleak and deadlock on win32
        if on_windows:
            return
        from pida.utils.launchpadder.gtkgui import PasswordDialog

        pass_dlg = PasswordDialog(self.svc.opt('launchpad_email_addr'))
        def pass_response(dlg, resp):
            dlg.hide()
            if resp == gtk.RESPONSE_ACCEPT:
                self.email, self.password = dlg.get_user_details()
                self.svc.set_opt('launchpad_email_addr', self.email)
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
            self.on_report
        )

    def on_report(self, action):
        if action.get_active():
            self.svc.show_report()
        else:
            self.svc.hide_report()


class BugreportOptions(OptionsConfig):

    def create_options(self):
        self.create_option(
            'launchpad_email_addr',
            _('Launchpad Email address'),
            str,
            '',
            _('Default Launchpad email address'),
            None,
        )


# Service class
class Bugreport(Service):
    """Describe your Service Here""" 

    actions_config = BugreportActions
    options_config = BugreportOptions

    def start(self):
        self._view = BugreportView(self)
    
    def show_report(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)

    def hide_report(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

# Required Service attribute for service loading
Service = Bugreport



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
