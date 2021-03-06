# -*- coding: utf-8 -*- 

from __future__ import print_function
# stdlib
import subprocess
import os

import execnet
import gtk

# PIDA Imports
from . import pidanose

# core
from pida.core.service import Service
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_TOGGLE
from pygtkhelpers.ui.objectlist import Column, Cell

# ui
from pida.ui.views import PidaView

# utils
from pygtkhelpers.gthreads import GeneratorTask, AsyncTask, gcall

# locale
from pida.core.locale import Locale
locale = Locale('nosetest')
_ = locale.gettext


status_map= { # 1 is for sucess, 2 for fail
              # used for fast tree updates
    'success': 'gtk-apply',
    'failure': 'gtk-no',
    'error': 'gtk-cancel',
    'mixed': 'gtk-dialog-warning',
    'running': 'gtk-refresh',
}


mapping = {
    'success': 'add_success',
    'error': 'add_error',
    'failure': 'add_failure',
    'start_ctx': 'start_context',
    'stop_ctx': 'stop_context',
    'start': 'start_test',
    'stop': 'stop_test',
}


class NoseTester(object):
    def __init__(self, view, channel):
        self.tree = {}
        self.stack = [ None ]

        self.view = view
        self.channel = channel
        channel.setcallback(lambda msg: gcall(self.callback, *msg))

    def __repr__(self):
        return '<test dispatcher %s>' % (self.channel,)

    def close(self):
        self.channel.close()

    def task(self):
        for item in self.channel:
            print(item)
            yield item

    def callback(self, kind, *message):
        if message is self:
            return # end of stream
        else:
            method = getattr(self, mapping[kind])
            method(*message)

    def start_test(self, test, *ignored):
        item = TestItem(test, self.stack[-1])
        self.view.append(item, parent=self.stack[-1])
        self.stack.append(item)
        self.view.expand_item(item.parent)

    def stop_test(self, *ignored):
        self.view.update(self.stack[-1])
        self.stack.pop()

    def add_success(self, test, error):
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
        self.view.append(item, parent=self.stack[-1])
        self.stack.append(item)
        if item.parent is not None:
            self.view.expand_item(item.parent)

    def stop_context(self):
        #XXX: new status
        current = self.stack.pop()
        if not current.children:
            self.view.remove(current)
            return

        states = set(x.status for x in current.children.itervalues())
        if len(states) > 1:
            current.status = 'mixed'
        else:
            current.status = iter(states).next()

        self.view.update(current)
        if current.status == 'success':
            self.view.collapse_item(current)

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
        return getattr(self, 'trace', 'Nothing is wrong directly here, i think')

class TestResultBrowser(PidaView):

    key = 'nosetests.results'

    gladefile = 'python_testresult_browser'
    locale = locale
    icon_name = 'python-icon'
    label_text = _('TestResults')

    def create_ui(self):
        self.tester = None
        self._group = execnet.Group()
        self.source_tree.set_columns([Column(title='Result', cells=[
                Cell('icon', use_stock=True, expand=False),
                Cell('short_name', title='status',),
            ])])
        self.source_tree.set_headers_visible(False)
        self.clear()

    def clear(self):
        self.source_tree.clear()


    def can_be_closed(self):
        self.svc.get_action('show_test_python').set_active(False)

    def run_tests(self):
        if self.tester:
            self.tester.close()
            self.tester = None
        self.clear()
        project = self.svc.boss.cmd('project','get_current_project')
        if not project:
            self.svc.notify_user(_("No project found"))
            return
        src = project.source_directory

        gw = self._group.makegateway()
        channel = gw.remote_exec(pidanose)
        channel.send(str(src))
        self.tester = NoseTester(self.source_tree, channel)

    def on_source_tree__item_activated(self, tv, item):
            self.svc.show_result(item.output)


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
            gtk.Action,
            _('Python Unit Tester'),
            _('Run the python unitTester'),
            'gtk-apply',
            self.on_test,
        )
        self.create_action(
            'show_test_python',
            gtk.ToggleAction,
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

    def start(self):
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
