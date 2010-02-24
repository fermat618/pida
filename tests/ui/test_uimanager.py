
from unittest import TestCase

import gtk

from pida.utils.testing import refresh_gui

from pida.ui.uimanager import PidaUIManager

class UIMSetupTestCase(TestCase):

    def setUp(self):
        self.uim = PidaUIManager()
        refresh_gui()

    def test_base_xml(self):
        self.assert_('main_menu' in self.uim._uim.get_ui())
        self.assert_('main_toolbar' in self.uim._uim.get_ui())

    def test_menu_file(self):
        self.assert_('FileMenu' in self.uim._uim.get_ui())

    def test_menu_edit(self):
        self.assert_('EditMenu' in self.uim._uim.get_ui())

    def test_menu_project(self):
        self.assert_('ProjectMenu' in self.uim._uim.get_ui())

    def test_menu_tools(self):
        self.assert_('ToolsMenu' in self.uim._uim.get_ui())

    def test_menu_view(self):
        self.assert_('ViewMenu' in self.uim._uim.get_ui())

    def test_menu_help(self):
        self.assert_('HelpMenu' in self.uim._uim.get_ui())

    def test_menu_actions_file(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('FileMenu' in a)

    def test_menu_actions_edit(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('EditMenu' in a)

    def test_menu_actions_project(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('ProjectMenu' in a)

    def test_menu_actions_language(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('LanguageMenu' in a)

    def test_menu_actions_tools(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('ToolsMenu' in a)

    def test_menu_actions_view(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('ViewMenu' in a)

    def test_menu_actions_help(self):
        a = [a.get_name() for a in self.uim._base_ag.list_actions()]
        self.assert_('HelpMenu' in a)

    def test_menubar(self):
        menubar = self.uim.get_menubar()
        refresh_gui()
        self.assert_(isinstance(menubar, gtk.MenuBar))
        [self.assert_(isinstance(m, gtk.MenuItem)) for m in menubar.get_children()]

    def test_toolbar(self):
        toolbar = self.uim.get_toolbar()
        toolbar  # pyflakes
        refresh_gui()

    def test_add_ui(self):
        ag = gtk.ActionGroup(name='myacts')
        ag.add_actions(
            [
                ('MyMenu', None, 'MyMenu', None, None),
            ]
        )
        self.uim.add_action_group(ag)
        self.uim.add_ui_from_string(
            """<menubar name="main_menubar">
                <menu name="FileMenu" action="FileMenu">
                    <menuitem action="MyMenu" />
                </menu>
            </menubar>"""
        )
        refresh_gui()
        menubar = self.uim.get_menubar()
        fm = menubar.get_children()[0]
        acts = [m.get_action().get_name() for m in fm.get_submenu() if m.get_action() is not None]
        self.assert_('MyMenu' in acts)


