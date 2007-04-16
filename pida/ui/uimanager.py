
import gtk

from pida.core.environment import get_uidef_path


base_menu_actions = [
    ('FileMenu', None, 'File', '<Alt>f', 'File Menu', None),
    ('EditMenu', None, 'Edit', '<Alt>e', 'Edit Menu', None),
    ('ProjectMenu', None, 'Project', '<Alt>p', 'Project Menu', None),
    ('LanguageMenu', None, 'Language', '<Alt>l', 'Language Menu', None),
    ('ToolsMenu', None, 'Tools', '<Alt>t', 'Tools Menu', None),
    ('ToolsDebug', None, 'Debug Pida', '', 'Debug Pida Menu', None),
    ('ViewMenu', None, 'View', '<Alt>v', 'View Menu', None),
    ('HelpMenu', None, 'Help', '<Alt>h', 'Help Menu', None),
]


class PidaUIManager(object):

    def __init__(self):
        self._uim = gtk.UIManager()
        self._ags = {}
        self._load_base_actions()
        self._load_base_ui()

    def _load_base_ui(self):
        uidef = get_uidef_path('base.xml')
        self.add_ui_from_file(uidef)

    def _load_base_actions(self):
        self._base_ag = gtk.ActionGroup(name='base_actions')
        self._base_ag.add_actions(base_menu_actions)
        self.add_action_group(self._base_ag)

    def add_action_group(self, group):
        self._uim.insert_action_group(group, len(self._ags))
        self._ags[group.get_name()] = group
        self.ensure_update()

    def get_toolbar(self):
        return self._uim.get_toplevels(gtk.UI_MANAGER_TOOLBAR)[0]

    def get_menubar(self):
        return self._uim.get_toplevels(gtk.UI_MANAGER_MENUBAR)[0]

    def add_ui_from_file(self, path):
        self._uim.add_ui_from_file(path)
        self.ensure_update()

    def add_ui_from_string(self, string):
        self._uim.add_ui_from_string(string) 
        self.ensure_update()
        
    def ensure_update(self):
        self._uim.ensure_update()

