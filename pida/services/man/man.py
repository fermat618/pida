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

import os
import gtk
import commands
import re
import cgi

from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaView

from pida.utils.gthreads import GeneratorTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('man')
_ = locale.gettext

class ManItem(object):

    def __init__(self, pattern, number, manpage):
        self.pattern = pattern
        self.number = number
        self.manpage = manpage
        self.markup = '%s(<span color="#0000c0">%d</span>) %s' % (cgi.escape(self.pattern), int(self.number), cgi.escape(self.manpage))

class ManView(PidaView):

    icon_name = 'gtk-library'
    label_text = 'Man'
    
    def create_ui(self):
        self.__vbox = gtk.VBox(spacing=3)
        self.__vbox.set_border_width(6)
        self.__entry = gtk.Entry()
        self.__entry.connect('changed', self.cb_entry_changed)
        self.__list = ObjectList(
               [
                   Column('markup', title='Man page', sorted=True, use_markup=True),
               ]
        )
        self.__list.connect('double-click', self._on_man_double_click)
        self.__list.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.__vbox.pack_start(self.__entry, expand=False)
        self.__vbox.pack_start(self.__list)
        self.add_main_widget(self.__vbox)
        self.__vbox.show_all()

    def clear_items(self):
        gcall(self.__list.clear)

    def add_item(self, item):
        self.__list.append(item)

    def _on_man_double_click(self, olist, item):
        commandargs = ['/usr/bin/man', item.number, item.pattern]
        directory = os.path.dirname(commandargs[0])
        self.svc.boss.cmd('commander', 'execute',
                commandargs=commandargs,
                cwd=directory,
                icon='gnome-library',
                title=_('Man %(pattern)s(%(number)d)') %
                {pattern:item.pattern, number:int(item.number)})
        ## show man page in terminal
        pass

    def cb_entry_changed(self, w):
        gcall(self.svc.cmd_find, pattern=w.get_text())


class ManActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_man',
            TYPE_TOGGLE,
            _('Man Viewer'),
            _('Show the man'),
            '',
            self.on_show_man,
            '<Shift><Control>m',
        )

    def on_show_man(self, action):
        if action.get_active():
            self.svc.show_man()
        else:
            self.svc.hide_man()

# Service class
class Man(Service):
    """Show manpage of command"""

    actions_config = ManActions

    def start(self):
        self._view = ManView(self)
        self._has_loaded = False
        self.counter = 0
        self.task = None

    def show_man(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_man(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def _cmd_find_add_item(self, counter, item):
        if ( self.counter != counter ):
            return
        self._view.add_item(item)

    def cmd_find(self, pattern):
        if ( len(pattern) > 1 ):
            self.counter = self.counter + 1
            self._view.clear_items()
            self.task = GeneratorTask(self._cmd_find, self._cmd_find_add_item)
            self.task.start(self.counter, pattern)

    def _cmd_find(self, counter, pattern):
        if ( self.counter != counter ):
            return
        cmd = 'man -f "%s"' % pattern
        ret = commands.getoutput(cmd)
        results = ret.split('\n')
        for result in results:
            if ( self.counter != counter ):
                return
            reman = re.compile('[(]([\d]+)[)]')
            list = reman.findall(result)
            if not len(list):
                continue
            name = result.split('(')[0].strip()
            res = result.split('- ',1)
            yield counter, ManItem(name, list[0], res[1])


# Required Service attribute for service loading
Service = Man



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
