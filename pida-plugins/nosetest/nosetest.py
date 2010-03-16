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

# stdlib
import subprocess
import os
from xml.sax.saxutils import escape

from xml.etree.ElementTree import iterparse
# gtk
import gtk

# kiwi
from pygtkhelpers.ui.objectlist import Column

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE
from pida.core.pdbus import DbusConfig, EXPORT

# ui
from pida.ui.views import PidaView, PidaGladeView

# utils
from pida.utils.gthreads import GeneratorTask, AsyncTask

# locale
from pida.core.locale import Locale
locale = Locale('nosetest')
_ = locale.gettext

export = EXPORT(suffix='nosetest')



class NosetestDBusConfig(DbusConfig):

    @export(sender_keyword='sender',  in_signature='s')
    def beginProcess(self, cwd, sender):
        self.svc.log.info('beginning suite of %s in %s', sender, cwd)
        self.sender = sender
        self.svc._tests.clear()

    @export(sender_keyword='sender')
    def endProcess(self, sender):
        pass

    @export(sender_keyword='sender', in_signature='s')
    def addSuccess(self, test, sender):
        if sender == self.sender:
            self.svc._tests.add_success(test)

    @export(sender_keyword='sender', in_signature='ss')
    def addError(self, test, err, sender):
        if sender == self.sender:
            self.svc._tests.add_error(test, err)

    @export(sender_keyword='sender', in_signature='ss')
    def addFailure(self, test, err, sender):
        if sender == self.sender:
            self.svc._tests.add_failure(test, err)

    @export(sender_keyword='sender', in_signature='ss')
    def startContext(self, name, file, sender):
        if sender == self.sender:
            self.svc._tests.start_context(name, file)

    @export(sender_keyword='sender')
    def stopContext(self, sender):
        if sender == self.sender:
            self.svc._tests.stop_context()

    @export(sender_keyword='sender', in_signature='s')
    def startTest(self, test, sender):
        if sender == self.sender:
            self.svc._tests.start_test(test)

    @export(sender_keyword='sender')
    def stopTest(self, sender):
        if sender == self.sender:
            self.svc._tests.stop_test()

status_map= { # 1 is for sucess, 2 for fail
              # used for fast tree updates
        'success': 'gtk-apply',
        'failure': 'gtk-no',
        'error': 'gtk-cancel',
        'mixed': 'gtk-dialog-warning',
        'running': 'gtk-refresh',
        }

def parse_test_name (self, name):
    if '(' in name:
        group, name = name.split('(', 2)
        return name[:-1], tuple(group.split('.'))
    else:
        groups = tuple(name.split('.'))
        return groups[-1], groups[:-1]


class TestItem(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.children = {}
        self.status = 'running'
        if parent is not None:
            parent.children[self.name] = self

    @property
    def short_name(self):
        if self.parent is None:
            return self.name
        else:
            return self.name[len(self.parent.name)+1:]

    @property
    def icon(self):
        return status_map[self.status]


    @property
    def output(self):
        return getattr(self, trace, 'Nothing is wrong directly here, i think')

class TestResultBrowser(PidaGladeView):

    key = 'nosetests.results'

    gladefile = 'python_testresult_browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('TestResults')

    def __init__(self,* k,**kw):
        PidaGladeView.__init__(self,*k,**kw)
        self.clear()

    def create_ui(self):
        self.source_tree.set_columns([
                Column('icon', use_stock=True, justify=gtk.JUSTIFY_LEFT),
                Column('short_name', title='status',),
            ])
        self.source_tree.set_headers_visible(False)

    def clear(self):
        self.source_tree.clear()
        self.tree = {}
        self.stack = [ None ]


    def can_be_closed(self):
        self.svc.get_action('show_test_python').set_active(False)

    def run_tests(self):
        project = self.svc.boss.cmd('project','get_current_project')
        if not project:
            self.svc.notify_user(_("No project found"))
            return
        src = project.source_directory
        def call(*k, **kw): 
            subprocess.call(*k, **kw)

        AsyncTask(call).start([
                    os.path.join(os.path.dirname(__file__), 'pidanose.py'),
                    '--with-dbus-reporter', '-q',
                ],
                cwd=src,
        )

    def on_source_tree__item_activated(self, tv, item):
            self.svc.show_result(item.output)

    def start_test(self, test):
        item = TestItem(test, self.stack[-1])
        self.source_tree.append(self.stack[-1], item)
        self.stack.append(item)
        self.source_tree.expand(item.parent)

    def stop_test(self):
        self.source_tree.update(self.stack[-1])
        self.stack.pop()

    def add_success(self, test):
        if self.stack[-1]:
            self.stack[-1].status = 'success'

    def add_error(self, test, error):
        if self.stack[-1]:
            item = self.stack[-1]
            item.status = 'error'
            item.trace = error

    def add_failure(self, test, error):
        if self.stack[-1]:
            item = self.stack[-1]
            item.status = 'failure'
            item.trace = error

    def start_context(self, name, file):
        item = TestItem(name, self.stack[-1])
        item.file = file
        self.source_tree.append(self.stack[-1], item)
        self.stack.append(item)
        if item.parent is not None:
            self.source_tree.expand(item.parent)

    def stop_context(self):
        #XXX: new status
        current = self.stack.pop()
        if not current.children:
            self.source_tree.remove(current)
            return

        states = set(x.status for x in current.children.itervalues())
        if len(states) > 1:
            current.status = 'mixed'
        else:
            current.status = iter(states).next()

        self.source_tree.update(current)
        if current.status == 'success':
            self.source_tree.collapse(current)


class TestOutputView(PidaView):

    key = 'nosetests.output'

    locale = locale
    icon_name = 'python-icon'
    label_text = _('TestResults')


    def create_ui(self):
        hb = gtk.HBox()
        self.add_main_widget(hb)
        sb = gtk.ScrolledWindow()
        sb.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sb.set_shadow_type(gtk.SHADOW_IN)
        sb.set_border_width(3)
        self._trace = gtk.TextView()
        self._trace.set_left_margin(6)
        self._trace.set_right_margin(6)
        sb.add(self._trace)
        hb.pack_start(sb)
        hb.show_all()

    def set_result(self, trace):
        self._trace.get_buffer().set_text(trace)

    def can_be_closed(self):
        self.svc.output_visible = False
        #we need this to remove the id (looks like moo bug)
        self.svc.boss.cmd('window', 'remove_view', view=self)
        return False


class PythonActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'test_python',
            TYPE_NORMAL,
            _('Python Unit Tester'),
            _('Run the python unitTester'),
            'gtk-apply',
            self.on_test,
        )
        self.create_action(
            'show_test_python',
            TYPE_TOGGLE,
            _('Python Unit Tester'),
            _('Show the python unitTester'),
            'none',
            self.on_toggle_results,
        )

    def on_toggle_results(self, action):
        if action.get_active():
            self.svc.show_results()
        else:
            self.svc.hide_results()

    def on_test(self, action):
        show_action = self.get_action('show_test_python')
        if not show_action.get_active():
            show_action.activate()
        self.svc.run_tests()


# Service class
class PythonTestResults(Service):
    """Service for all things Python""" 

    actions_config = PythonActionsConfig
    dbus_config = NosetestDBusConfig

    def pre_start(self):
        """Start the service"""
        self._tests = TestResultBrowser(self)
        self.output_visible = False
        self._view = TestOutputView(self)


    def show_results(self):
        self.boss.cmd('window', 'add_view', 
                paned='Plugin', view=self._tests)

    def hide_results(self):
        self.boss.cmd('window', 'remove_view', view=self._tests)

    def show_result(self, result):
        self._view.set_result(result)
        if not self.output_visible:
            self.boss.cmd('window', 'add_view', 
                    paned='Terminal', view=self._view)
            self.output_visible = True
        else:
            self.boss.cmd('window', 'present_view', view=self._view)

    def stop(self):
        if self.get_action('show_test_python').get_active():
            self.hide_results()
        if self.output_visible:
            self.boss.cmd('window', 'remove_view', view =self._view)

    def run_tests(self):
        self._tests.run_tests()

# Required Service attribute for service loading
Service = PythonTestResults



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
