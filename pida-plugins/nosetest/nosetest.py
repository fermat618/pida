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
from kiwi.ui.objectlist import Column

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE

# ui
from pida.ui.views import PidaView, PidaGladeView

# utils
from pida.utils.gthreads import GeneratorTask

# locale
from pida.core.locale import Locale
locale = Locale('nosetest')
_ = locale.gettext


class TraceItem(object):
    def __init__(self, **kw):
        for name in 'text file function line'.split():
            setattr(self, name, kw[name])

    def __str__(self):
        return 'File %r, line %s, in %s'%(self.file, self.line, self.function)

    @property
    def markup(self):
        return '  %s'%self


class Trace(object):
    def __init__(self, type, args):
        self.type = type
        self.args = args
        self.items = []

    @staticmethod
    def from_element(element):
        cause = element.find('cause')
        if cause is None:
            return
        type = cause.attrib['type']
        args = escape(cause.findtext(''))

        #XXX: unescape hack, find a better one in the stdlib
        #for f, t in zip('&lt; &gt; &quot; &apos; &amp;'.split(), '<>"\'&'):
        #    args = args.replace(f, t)
        #args = args.strip()

        trace = Trace(type, args)
        trace.items.extend(TraceItem(**x.attrib) 
                                  for x in element.findall('frame'))

        # XXX: captured output support
        return trace
    
    @property
    def markup(self):
        return '%s: %s'%(self.type, self.args)

    def __str__(self):
        lines = ['Traceback:']
        lines.extend(x.markup for x in self.items)
        lines.append(self.markup)
        return '\n'.join(lines)

class TestResult(object) : 
    status_map= { # 1 is for sucess, 2 for fail
                  # used for fast tree updates
            'success': ('gtk-ok', 1),
            'failure': ('gtk-no', 2),
            'error': ('gtk-cancel', 2),
            }

    parent = None
    trace = None

    def __init__(self, full_name, status, trace, capture):
        print full_name, status, trace, capture
        self.full_name = full_name
        self.trace = trace
        self.capture = capture
        self.name, self.group_names = self.parse_test_name(full_name)
        status = status.lower()
        self.status, self.state = self.status_map[status]

    def parse_test_name (self, name):
        if '(' in name:
            group, name = name.split('(', 2)
            return name[:-1], tuple(group.split('.'))
        else:
            groups = tuple(name.split('.'))
            return groups[-1], groups[:-1]

    def parents(self): 
        p = self.parent

        while p.parent:
            yield p
            p = p.parent

    @property
    def output(self):
        if self.trace:
            return str(self.trace)
        else:
            return 'Success'

class TestResultGroup(object):
    state_map = {
            0: 'gtk-directory',
            1: 'gtk-ok',
            2: 'gtk-dialog-error',
            3: 'gtk-dialog-question',
            }

    def __init__(self,  names, parent):
        self.name = names and names[-1] or None
        self.names = names
        self.parent = parent
        self.state = 0
        self.status = 'gtk-directory'

    def add_child(self,  child):
        res = child.state | self.state
        if res != self.state:
            self.state = res
            self.status = self.state_map[res]
            return True

    @property
    def output(self):
        return 'TestResultGroup %s'% '.'.join(self.names)

class TestResultBrowser(PidaGladeView):

    key = 'nosetests.results'

    gladefile = 'python-testresult-browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('TestResults')

    def __init__(self,* k,**kw):
        PidaGladeView.__init__(self,*k,**kw)
        self.items = {}
        self.tree = {(): TestResultGroup(None, None)}
        self.gt = None

    def create_ui(self):
        self.source_tree.set_columns([
                Column('status', use_stock=True, justify=gtk.JUSTIFY_LEFT),
                Column('name', title='status',),
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

    def add_test_tree(self , test):
        names = test.group_names
        group = self.get_or_create_testgroup(names)
        test.parent = group
        #self.source_tree.append(group,test)
        self.source_tree.append(None, test)

        for parent in test.parents():
            if parent.add_child(test):
                self.source_tree.update(parent)
            else:
                break

        if test.state == 2:
            for parent in reversed(list(test.parents())):
                self.source_tree.expand(parent, open_all=False)



    def test_add(self, element):
        print element, str(element)
        attr = element.attrib
        name = 'name' # attr['id']
        status = attr['status']

        trace = None
        capture = None

        test = TestResult(name, status, trace, capture) #XXX add traces
        
        trace = Trace.from_element(element)
        if trace:
            test.trace = trace

        self.items[test.full_name] = test
        self.add_test_tree(test)

    def run_tests(self):
        if self.gt:
            self.svc.log.info('tried to start nosetests twice')
            return

        self.clear_items()
        gt = GeneratorTask(self.test_task, self.test_add, self.test_done)
        gt.start()
        self.gt = gt

    def test_done(self):
        self.gt = None

    def test_task(self):
        """
        reads the test ouput from nosetest verbose
        very untested code ;)
        """

        project = self.svc.boss.cmd('project','get_current_project')
        if not project:
            self.svc.notify_user(_("No project found"))
            return
        src = project.source_directory
        proc = subprocess.Popen(
                [os.path.join(os.path.dirname(__file__),'pidanose.py'),
                '--with-xml-output'],
                cwd=src,
                 stdout=None,
                 stdin=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                )

        for event, element in iterparse(proc.stderr):
            print event, element
            if element.tag == 'result':
                yield element

    def on_source_tree__double_click(self, tv, item):
            self.svc.show_result(item)

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

    def set_result(self, result):
        self._trace.get_buffer().set_text(result.output)

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
