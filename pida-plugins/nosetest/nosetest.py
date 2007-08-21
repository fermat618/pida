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
import sys
import subprocess
import re

from cgi import escape

# gtk
import gtk

# kiwi
from kiwi.ui.objectlist import ObjectList, Column

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE
from pida.core.options import OptionsConfig, OTypeString
from pida.core.features import FeaturesConfig
from pida.core.projects import ProjectController,  ProjectKeyDefinition
from pida.core.interfaces import IProjectController

# ui
from pida.ui.views import PidaView, PidaGladeView
from pida.ui.htmltextview import HtmlTextView


# utils
from pida.utils import pyflakes
from pida.utils import pythonparser
from pida.utils.gthreads import AsyncTask, GeneratorTask

# locale
from pida.core.locale import Locale
locale = Locale('nosetest')
_ = locale.gettext

testcase_re = re.compile(r'(?P<name>\w+) \((?P<case>[\w\.]+)\)')

### Pyflakes
class TestResult:
    status_map= { # 1 is for sucess, 2 for fail
                  # used for fast tree updates
            'ok': ('gtk-apply', 1),
            'fail': ('gtk-no', 2),
            'error': ('gtk-cancel', 2),
            }

    output = ''
    parent = None
    def __init__(self, line):
        self.full_name, status = line.rsplit(' ... ', 2)
        self.name = self.parse_test_name()
        status = status.lower()
        self.status, self.state = self.status_map[status]
    
    def parse_test_name(self):
        match = testcase_re.match(self.full_name)
        if match:
            name = match.group('name')
            self.testgroup_names = tuple(match.group('case').split('.'))
            return name
        else:
            dt = 'Doctest: '
            if self.full_name.startswith(dt):
                self.full_name = self.full_name[len(dt):]
                pre = ('Doctest',)
            else:
                pre = ()

            s = self.full_name.split('.')
            self.testgroup_names = pre + tuple(s[:-1])
            
            return s[-1]

    def parents(self):
        p = self.parent
        while p.parent:
            yield p
            p = p.parent

class TestResultGroup:
    state_map = {
            0: 'gtk-directory',
            1: 'gtk-ok',
            2: 'gtk-dialog-error',
            3: 'gtk-dialog-question',
            }

    def __init__(self, names, parent):
        self.name = names and names[-1] or None
        self.names = names
        self.parent = parent
        self.state = 0
        self.status = 'gtk-directory'

    def add_child(self, child):
        res = child.state | self.state
        if res != self.state:
            self.state = res
            self.status = self.state_map[res]
            return True

    @property
    def output(self):
        return 'TestResultGroup %s'% '.'.join(self.names)

class TestResultBrowser(PidaGladeView):

    gladefile = 'python-testresult-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('TestResults')

    def __init__(self,*k,**kw):
        PidaGladeView.__init__(self,*k,**kw)
        self.items = {}
        self.tree = {(): TestResultGroup(None, None)}

    def create_ui(self):
        self.source_tree.set_columns([
                Column('status', use_stock=True),
                Column('name'),
            ])
        self.source_tree.set_headers_visible(False)

    def clear_items(self):
        self.source_tree.clear()
        self.items.clear()
        self.tree = {(): TestResultGroup(None, None)}


    def can_be_closed(self):
        self.svc.get_action('show_test_python').set_active(False)

    def get_or_create_testgroup(self, names):
        group = self.tree.get(names)
        if not group:
            parent = self.get_or_create_testgroup(names[:-1])
            group = TestResultGroup(names, parent)
            self.tree[names] = group
            a = self.source_tree.append
            if parent.name is None:
                a(None , group)
            else:
                a(parent, group)
        return group

    def add_test_tree(self, test):
        names = test.testgroup_names
        group = self.get_or_create_testgroup(tuple(names))
        test.parent = group
        self.source_tree.append(group,test)

        for parent in test.parents():
            if parent.add_child(test):
                self.source_tree.update(parent)
            else:
                break

        if test.state == 2:
            for parent in reversed(list(test.parents())):
                self.source_tree.expand(parent, open_all=False)



    def add_test(self, test):
        test = TestResult(test)
        self.items[test.full_name] = test
        self.add_test_tree(test)

    def append_test(self, name, output=None):
        if not output:
            self.add_test(name)
        else:
            self.items[name].output = output

    def run_tests(self):
        self.clear_items()
        gt = GeneratorTask(
                self.test_task,
                self.append_test,
                self.source_tree.refresh()
                )
        gt.start()
        self.gt = gt

    def test_task(self):
        """
        reads the test ouput from nosetest verbose
        very untested code ;)
        """

        project = self.svc.boss.cmd('project','get_current_project')
        src = project.source_directory
        proc = subprocess.Popen(
                ['nosetests','-v'],
                cwd=src,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )
        for line in proc.stderr:
            line = line.rstrip()
            if not line:
                break
            yield line
        next_test = '='*70+'\n'
        next_block = '-'*70+'\n'
        name = None
        output = []
        f = proc.stderr

        for line in f:
            if line == '='*70+'\n':
                if output:
                    out = ''.join(output)
                    yield name, out
                    output = []
                name = f.next().rstrip()
                name = name[name.find(':')+2:]

                while f.next() != next_block: pass
                continue

            output.append(line)



    def on_source_tree__double_click(self, tv, item):
            self.svc.show_result(item)

class TestOutputView(PidaView):
    
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
        self._html = HtmlTextView()
        self._html.set_left_margin(6)
        self._html.set_right_margin(6)
        sb.add(self._html)
        hb.pack_start(sb)
        hb.show_all()

    def set_result(self, result):
        data = '<pre>%s</pre>'%escape(result.output)
        self._html.clear_html()
        self._html.display_html(data)

    def can_be_closed(self):
        self.svc.output_visible = False
        return True

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
            self.on_show_results,
        )

    def on_show_results(self, action):
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

    def pre_start(self):
        """Start the service"""
        self._tests = TestResultBrowser(self)
        self.output_visible = False
        self._view = TestOutputView(self)


    def show_results(self):
        self.boss.cmd('window', 'add_view',
            paned='Plugin', view=self._tests.get_view())

    def hide_results(self):
        self.boss.cmd('window', 'remove_view',
            view=self._tests.get_view())

    def show_result(self, result):
        self._view.set_result(result)
        if not self.output_visible:
            self.boss.cmd('window', 'add_view',
                paned='Terminal', view=self._view.get_view())
            self.output_visible = True



    def stop(self):
        if self.get_action('show_test_python').get_active():
            self.hide_results()

    def run_tests(self):
        self._tests.run_tests()

# Required Service attribute for service loading
Service = PythonTestResults



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
