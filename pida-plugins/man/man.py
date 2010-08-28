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

from pygtkhelpers.ui.objectlist import ObjectList, Column

# PIDA Imports
from pida.core.service import Service
from pida.core.actions import ActionsConfig
from pida.core.features import FeaturesConfig
from pida.core.actions import TYPE_REMEMBER_TOGGLE

from pida.ui.views import PidaView, WindowConfig

from pida.utils.gthreads import GeneratorSubprocessTask

# locale
from pida.core.locale import Locale
locale = Locale('man')
_ = locale.gettext

class ManItem(object):

    def __init__(self, pattern, number, description, search):
        self.pattern = pattern
        self.number = number
        self.description = self._color_match(cgi.escape(description), search)
        patternmark = self._color_match(cgi.escape(pattern), search)
        self.markup = '%s(<span color="#0000cc">%d</span>)' % (
            patternmark, int(self.number))

    def _color_match(self, data, match):
        return data.replace(match, '<span color="#c00000"><b>%s</b></span>' % match)


class ManView(PidaView):

    key = 'man.form'

    icon_name = 'gtk-library'
    label_text = 'Man'

    def create_ui(self):
        self.vbox = gtk.VBox(spacing=3)
        self.vbox.set_border_width(6)
        self.hbox = gtk.HBox()
        self.entry = gtk.Entry()
        self.check = gtk.CheckButton(label='-k')
        self.list = ObjectList([
                   Column('markup', title=_('Man page'), sorted=True,
                       use_markup=True),
                   Column('description', title=_('Description'),
                       use_markup=True),
               ])
        self.scroll = gtk.ScrolledWindow()
        self.scroll.add(self.list)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.hbox.pack_start(self.entry)
        self.hbox.pack_start(self.check, expand=False)
        self.vbox.pack_start(self.hbox, expand=False)
        self.vbox.pack_start(self.scroll)
        self.add_main_widget(self.vbox)
        self.vbox.show_all()

    def clear_items(self):
        self.list.clear()

    def add_item(self, item):
        self.list.append(item)

    def close(self, term, dummy):
        term.close_view()

    def open(self, item):
        commandargs = ['/usr/bin/env', 'man', item.number, item.pattern]
        directory = os.path.dirname(commandargs[0])
        self.svc.boss.cmd('commander', 'execute',
                commandargs=commandargs,
                cwd=directory,
                icon='gnome-library',
                eof_handler=self.close,
                title='%(pattern)s(%(number)d)' % dict(
                    pattern=item.pattern,
                    number=int(item.number)
                ))

    def on_list__item_activated(self, olist, item):
        self.open(item)

    def on_entry__changed(self, w):
        if self.check.get_active():
            options = '-k'
        else:
            options = '-f'
        self.svc.cmd_find(options=options, pattern=self.entry.get_text())
    on_check__toggled = on_entry__changed

    def can_be_closed(self):
        self.svc.get_action('show_man').set_active(False)


class ManActions(ActionsConfig):

    def create_actions(self):
        ManWindowConfig.action = self.create_action(
            'show_man',
            TYPE_REMEMBER_TOGGLE,
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

class ManWindowConfig(WindowConfig):
    key = ManView.key
    label_text = ManView.label_text


class ManFeaturesConfig(FeaturesConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('window', 'window-config',
            ManWindowConfig)

# Service class
class Man(Service):
    """Show manpage of command"""

    actions_config = ManActions
    features_config = ManFeaturesConfig

    def start(self):
        self._view = ManView(self)
        self._has_loaded = False
        self.task = None

    def show_man(self):
        self.boss.cmd('window', 'add_view', paned='Terminal', view=self._view)
        if not self._has_loaded:
            self._has_loaded = True

    def hide_man(self):
        self.boss.cmd('window', 'remove_view', view=self._view)

    def cmd_find(self, options, pattern):

        # stop and clear task
        if self.task:
            self.task.stop()
        self._view.clear_items()

        # don't make empty search
        if not pattern:
            return

        # prepare command
        cmd = '/usr/bin/env man %s "%s"' % (options, pattern)
        #XXX: unittest
        reman = re.compile(r'''
            (?P<name>\w+)
            \s*(\[\])\s* #whitespace and gentoo brackets
            \((?P<group>[\w\d]+)\)
            \s*-\s*
            (?P<desc>.*)
            ''', re.VERBOSE)

        # match and add each line
        def _line(result):
            # avoid too many results
            if len(self._view.list) > 100:
                self.task.stop()

            match = reman.match(result)
            if not match:
                return
            name = match.group('name')
            group = match.group('group')
            desc = match.group('desc')


            # add in list
            self._view.add_item(ManItem(name, group, desc, pattern))

        # launch man subprocess
        self.task = GeneratorSubprocessTask(_line)
        self.task.start(cmd, shell=True)

    def stop(self):
        if self.task:
            self.task.stop()
        if self.get_action('show_man').get_active():
            self.hide_man()


# Required Service attribute for service loading
Service = Man



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
